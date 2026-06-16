"""Graph data structures for supply chain network modeling."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional


class LocationType(Enum):
    """Classification of nodes in the supply chain network."""

    FACTORY = "Factory"
    WAREHOUSE = "Warehouse"
    OUTLET = "Outlet"


@dataclass(frozen=True)
class Location:
    """A supply chain hub represented as a graph node.

    Attributes:
        name: Human-readable city or hub identifier.
        location_type: Whether the hub is a factory, warehouse, or outlet.
        latitude: Approximate latitude for display and mock realism.
        longitude: Approximate longitude for display and mock realism.
    """

    name: str
    location_type: LocationType
    latitude: float
    longitude: float

    def __str__(self) -> str:
        return f"{self.name} ({self.location_type.value})"


@dataclass(frozen=True)
class TransitRoute:
    """A directed transit edge between two supply chain locations.

    Attributes:
        destination: Target location name (adjacency list key).
        distance_km: Physical route distance in kilometers.
        fuel_cost_inr: Estimated fuel and toll cost in Indian Rupees (INR).
        risk_factor: Operational risk score in [0.0, 1.0] (higher = riskier).
        transit_hours: Estimated travel time in hours.
    """

    destination: str
    distance_km: float
    fuel_cost_inr: float
    risk_factor: float
    transit_hours: float

    def __post_init__(self) -> None:
        if self.distance_km < 0:
            raise ValueError("distance_km must be non-negative")
        if self.fuel_cost_inr < 0:
            raise ValueError("fuel_cost_inr must be non-negative")
        if not 0.0 <= self.risk_factor <= 1.0:
            raise ValueError("risk_factor must be between 0.0 and 1.0")
        if self.transit_hours < 0:
            raise ValueError("transit_hours must be non-negative")


@dataclass
class Graph:
    """Directed weighted graph using an adjacency list.

    Nodes are supply chain locations keyed by name. Edges are transit routes
    stored as lists of ``TransitRoute`` objects per source node.

    Attributes:
        _locations: Mapping of location name to ``Location`` metadata.
        _adjacency_list: Mapping of source name to outgoing ``TransitRoute`` list.
    """

    _locations: Dict[str, Location] = field(default_factory=dict)
    _adjacency_list: Dict[str, List[TransitRoute]] = field(default_factory=dict)

    def add_location(self, location: Location) -> None:
        """Register a location as a graph node.

        Args:
            location: Location metadata to insert.

        Raises:
            ValueError: If a location with the same name already exists.

        Time Complexity:
            O(1) average-case hash map insertion.

        Space Complexity:
            O(1) additional space per node (excluding stored object).
        """
        if location.name in self._locations:
            raise ValueError(f"Location '{location.name}' already exists")
        self._locations[location.name] = location
        self._adjacency_list.setdefault(location.name, [])

    def add_route(
        self,
        source: str,
        destination: str,
        distance_km: float,
        fuel_cost_inr: float,
        risk_factor: float,
        transit_hours: float,
    ) -> None:
        """Add a directed transit route between two existing locations.

        Args:
            source: Origin location name.
            destination: Target location name.
            distance_km: Route distance in kilometers.
            fuel_cost_inr: Route fuel/toll cost in INR.
            risk_factor: Operational risk in [0.0, 1.0].
            transit_hours: Estimated travel time in hours.

        Raises:
            KeyError: If source or destination is not registered.

        Time Complexity:
            O(1) average-case to append to adjacency list.

        Space Complexity:
            O(1) additional space per edge object.
        """
        if source not in self._locations:
            raise KeyError(f"Unknown source location: {source}")
        if destination not in self._locations:
            raise KeyError(f"Unknown destination location: {destination}")

        route = TransitRoute(
            destination=destination,
            distance_km=distance_km,
            fuel_cost_inr=fuel_cost_inr,
            risk_factor=risk_factor,
            transit_hours=transit_hours,
        )
        self._adjacency_list[source].append(route)

    def get_location(self, name: str) -> Location:
        """Return location metadata by name.

        Args:
            name: Location identifier.

        Returns:
            Matching ``Location`` instance.

        Raises:
            KeyError: If the location does not exist.

        Time Complexity:
            O(1) average-case hash map lookup.

        Space Complexity:
            O(1).
        """
        return self._locations[name]

    def get_neighbors(self, source: str) -> List[TransitRoute]:
        """Return outgoing transit routes from a source location.

        Args:
            source: Origin location name.

        Returns:
            List of ``TransitRoute`` edges (may be empty).

        Time Complexity:
            O(1) average-case to fetch the adjacency list reference.

        Space Complexity:
            O(1) — returns a reference, not a copy.
        """
        if source not in self._adjacency_list:
            raise KeyError(f"Unknown location: {source}")
        return self._adjacency_list[source]

    def location_names(self) -> List[str]:
        """Return all registered location names in insertion order.

        Time Complexity:
            O(V) where V is the number of vertices.

        Space Complexity:
            O(V) for the returned list.
        """
        return list(self._locations.keys())

    def edge_count(self) -> int:
        """Return total number of directed edges in the graph.

        Time Complexity:
            O(V + E) — iterates all adjacency lists.

        Space Complexity:
            O(1).
        """
        return sum(len(routes) for routes in self._adjacency_list.values())

    def vertex_count(self) -> int:
        """Return number of vertices (locations).

        Time Complexity:
            O(1).

        Space Complexity:
            O(1).
        """
        return len(self._locations)

    def has_location(self, name: str) -> bool:
        """Check whether a location name is registered.

        Time Complexity:
            O(1) average-case.

        Space Complexity:
            O(1).
        """
        return name in self._locations

    def iter_routes(self) -> List[TransitRoute]:
        """Return a flat list of all directed transit routes in the graph.

        Time Complexity:
            O(E) — aggregates every adjacency list.

        Space Complexity:
            O(E) for the returned list.
        """
        routes: List[TransitRoute] = []
        for edge_list in self._adjacency_list.values():
            routes.extend(edge_list)
        return routes

    def get_route(self, source: str, destination: str) -> Optional[TransitRoute]:
        """Find a direct edge from source to destination, if present.

        Args:
            source: Origin location name.
            destination: Target location name.

        Returns:
            Matching ``TransitRoute`` or ``None``.

        Time Complexity:
            O(deg(source)) — linear scan of outgoing edges.

        Space Complexity:
            O(1).
        """
        for route in self.get_neighbors(source):
            if route.destination == destination:
                return route
        return None
