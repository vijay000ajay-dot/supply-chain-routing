"""Dijkstra-based supply chain route optimization."""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional, Tuple

from supply_chain.graph import Graph, TransitRoute
from supply_chain.min_heap import MinHeap


class RoutingMetric(Enum):
    """Selectable edge-weight strategy for path optimization."""

    SHORTEST_DISTANCE = "shortest_distance"
    LOWEST_COST = "lowest_cost"
    BALANCED_EFFICIENCY = "balanced_efficiency"


@dataclass
class RouteStep:
    """One hop in an optimized route trajectory.

    Attributes:
        from_location: Origin hub name for this leg.
        to_location: Destination hub name for this leg.
        distance_km: Leg distance in kilometers.
        fuel_cost_inr: Leg fuel/toll cost in INR.
        risk_factor: Leg operational risk score.
        transit_hours: Leg travel time in hours.
        cumulative_weight: Running optimized metric total at this step.
    """

    from_location: str
    to_location: str
    distance_km: float
    fuel_cost_inr: float
    risk_factor: float
    transit_hours: float
    cumulative_weight: float


@dataclass
class RouteResult:
    """Complete routing outcome from Dijkstra optimization.

    Attributes:
        source: Starting hub name.
        destination: Target hub name.
        metric: Routing metric used for optimization.
        path: Ordered list of location names from source to destination.
        steps: Detailed per-leg trajectory.
        total_distance_km: Sum of leg distances.
        total_fuel_cost_inr: Sum of leg fuel costs.
        total_transit_hours: Sum of leg travel times.
        max_risk_factor: Maximum risk among traversed legs.
        optimized_weight: Final Dijkstra path weight under chosen metric.
        vertices_relaxations: Count of distance improvements (for analysis).
        heap_operations: Count of heap insert/extract operations.
    """

    source: str
    destination: str
    metric: RoutingMetric
    path: List[str] = field(default_factory=list)
    steps: List[RouteStep] = field(default_factory=list)
    total_distance_km: float = 0.0
    total_fuel_cost_inr: float = 0.0
    total_transit_hours: float = 0.0
    max_risk_factor: float = 0.0
    optimized_weight: float = 0.0
    vertices_relaxations: int = 0
    heap_operations: int = 0


class DijkstraRouter:
    """Computes optimal supply chain routes using Dijkstra's algorithm.

    Uses a custom min-heap for frontier management and supports multiple
    edge-weighting strategies for logistics decision-making.
    """

    def __init__(self, graph: Graph) -> None:
        """Attach a supply chain graph to the router.

        Args:
            graph: Populated ``Graph`` instance.

        Time Complexity:
            O(1).

        Space Complexity:
            O(1) — stores reference only.
        """
        self._graph = graph
        self._normalization_cache: Optional[Dict[str, float]] = None

    def find_route(
        self,
        source: str,
        destination: str,
        metric: RoutingMetric,
    ) -> RouteResult:
        """Find an optimal route under the selected routing metric.

        Args:
            source: Starting location name.
            destination: Target location name.
            metric: Weighting strategy for edge costs.

        Returns:
            ``RouteResult`` with path, costs, and complexity counters.

        Raises:
            KeyError: If source or destination is unknown.
            ValueError: If no path exists between the endpoints.

        Time Complexity:
            O((V + E) log V) using binary min-heap:
            - Each vertex extracted at most once: O(V log V)
            - Each edge relaxed once with possible heap decrease-key: O(E log V)

        Space Complexity:
            O(V) for distance maps, predecessor map, visited set, and heap.
        """
        if not self._graph.has_location(source):
            raise KeyError(f"Unknown source: {source}")
        if not self._graph.has_location(destination):
            raise KeyError(f"Unknown destination: {destination}")

        if metric == RoutingMetric.BALANCED_EFFICIENCY:
            self._normalization_cache = self._compute_normalization_factors()
        else:
            self._normalization_cache = None

        distances: Dict[str, float] = {name: math.inf for name in self._graph.location_names()}
        predecessors: Dict[str, Optional[str]] = {name: None for name in self._graph.location_names()}
        visited: set[str] = set()

        distances[source] = 0.0
        heap = MinHeap()
        heap.insert(0.0, source)
        heap_operations = 0
        relaxations = 0

        while not heap.is_empty():
            current_dist, current = heap.extract_min()
            heap_operations += 1

            if current in visited:
                continue
            if current_dist > distances[current]:
                continue

            visited.add(current)
            if current == destination:
                break

            for route in self._graph.get_neighbors(current):
                neighbor = route.destination
                if neighbor in visited:
                    continue

                edge_weight = self._edge_weight(route, metric)
                candidate = distances[current] + edge_weight

                if candidate < distances[neighbor]:
                    distances[neighbor] = candidate
                    predecessors[neighbor] = current
                    heap.insert(candidate, neighbor)
                    heap_operations += 1
                    relaxations += 1

        if distances[destination] is math.inf:
            raise ValueError(
                f"No route exists from '{source}' to '{destination}'"
            )

        path = self._reconstruct_path(predecessors, source, destination)
        result = self._build_result(
            source=source,
            destination=destination,
            metric=metric,
            path=path,
            optimized_weight=distances[destination],
            relaxations=relaxations,
            heap_operations=heap_operations,
        )
        return result

    def _edge_weight(self, route: TransitRoute, metric: RoutingMetric) -> float:
        """Compute Dijkstra edge weight for a transit route.

        Args:
            route: Transit edge to evaluate.
            metric: Selected optimization strategy.

        Returns:
            Non-negative scalar weight for Dijkstra relaxation.

        Time Complexity:
            O(1) for distance/cost metrics; O(1) with cached norms for balanced.

        Space Complexity:
            O(1).
        """
        if metric == RoutingMetric.SHORTEST_DISTANCE:
            return route.distance_km

        if metric == RoutingMetric.LOWEST_COST:
            return route.fuel_cost_inr

        # Balanced efficiency: weighted sum of normalized distance, cost, and risk.
        assert self._normalization_cache is not None
        norm_distance = route.distance_km / self._normalization_cache["max_distance"]
        norm_cost = route.fuel_cost_inr / self._normalization_cache["max_cost"]
        norm_risk = route.risk_factor / self._normalization_cache["max_risk"]

        return (
            0.45 * norm_distance
            + 0.40 * norm_cost
            + 0.15 * norm_risk
        )

    def _compute_normalization_factors(self) -> Dict[str, float]:
        """Scan all edges to derive max values for balanced metric scaling.

        Time Complexity:
            O(E) — single pass over all adjacency lists.

        Space Complexity:
            O(1) — returns a fixed-size dictionary.
        """
        max_distance = 0.0
        max_cost = 0.0
        max_risk = 0.0

        for route in self._graph.iter_routes():
            max_distance = max(max_distance, route.distance_km)
            max_cost = max(max_cost, route.fuel_cost_inr)
            max_risk = max(max_risk, route.risk_factor)

        return {
            "max_distance": max(max_distance, 1.0),
            "max_cost": max(max_cost, 1.0),
            "max_risk": max(max_risk, 1.0),
        }

    def _reconstruct_path(
        self,
        predecessors: Dict[str, Optional[str]],
        source: str,
        destination: str,
    ) -> List[str]:
        """Rebuild vertex path from predecessor map.

        Time Complexity:
            O(L) where L is path length (≤ V).

        Space Complexity:
            O(L) for the reversed path list.
        """
        path: List[str] = []
        current: Optional[str] = destination
        while current is not None:
            path.append(current)
            current = predecessors[current]
        path.reverse()

        if not path or path[0] != source:
            raise ValueError("Failed to reconstruct valid path")
        return path

    def _build_result(
        self,
        source: str,
        destination: str,
        metric: RoutingMetric,
        path: List[str],
        optimized_weight: float,
        relaxations: int,
        heap_operations: int,
    ) -> RouteResult:
        """Assemble detailed route statistics from a vertex path.

        Time Complexity:
            O(L) where L is number of hops in the path.

        Space Complexity:
            O(L) for steps list.
        """
        steps: List[RouteStep] = []
        total_distance = 0.0
        total_cost = 0.0
        total_hours = 0.0
        max_risk = 0.0
        cumulative = 0.0

        for i in range(len(path) - 1):
            from_loc = path[i]
            to_loc = path[i + 1]
            route = self._graph.get_route(from_loc, to_loc)
            if route is None:
                raise ValueError(f"Missing edge: {from_loc} -> {to_loc}")

            leg_weight = self._edge_weight(route, metric)
            cumulative += leg_weight

            steps.append(
                RouteStep(
                    from_location=from_loc,
                    to_location=to_loc,
                    distance_km=route.distance_km,
                    fuel_cost_inr=route.fuel_cost_inr,
                    risk_factor=route.risk_factor,
                    transit_hours=route.transit_hours,
                    cumulative_weight=cumulative,
                )
            )
            total_distance += route.distance_km
            total_cost += route.fuel_cost_inr
            total_hours += route.transit_hours
            max_risk = max(max_risk, route.risk_factor)

        return RouteResult(
            source=source,
            destination=destination,
            metric=metric,
            path=path,
            steps=steps,
            total_distance_km=total_distance,
            total_fuel_cost_inr=total_cost,
            total_transit_hours=total_hours,
            max_risk_factor=max_risk,
            optimized_weight=optimized_weight,
            vertices_relaxations=relaxations,
            heap_operations=heap_operations,
        )

    @staticmethod
    def complexity_analysis(vertex_count: int, edge_count: int) -> Dict[str, str]:
        """Return Big-O breakdown strings for interview study.

        Args:
            vertex_count: Number of graph vertices (V).
            edge_count: Number of graph edges (E).

        Returns:
            Dictionary of labeled complexity notes.

        Time Complexity:
            O(1).

        Space Complexity:
            O(1).
        """
        return {
            "algorithm": "Dijkstra with binary min-heap",
            "time": f"O((V + E) log V) = O(({vertex_count} + {edge_count}) log {vertex_count})",
            "space": f"O(V) = O({vertex_count})",
            "heap_insert": "O(log V) per relaxation",
            "heap_extract_min": "O(log V) per settled vertex",
            "path_reconstruction": "O(L) where L ≤ V",
        }
