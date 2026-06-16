"""Mock supply chain network generator with Indian logistics hubs."""

from __future__ import annotations

import random
from typing import List, Tuple

from supply_chain.graph import Graph, Location, LocationType


class MockDataGenerator:
    """Builds a realistic mock supply chain graph for demos and testing.

    Populates ten Indian city hubs with mixed factory/warehouse/outlet roles
    and a connected directed route network with varying transit attributes.
    """

    _HUB_DEFINITIONS: List[Tuple[str, LocationType, float, float]] = [
        ("Mumbai", LocationType.FACTORY, 19.0760, 72.8777),
        ("Delhi", LocationType.WAREHOUSE, 28.7041, 77.1025),
        ("Chennai", LocationType.FACTORY, 13.0827, 80.2707),
        ("Bengaluru", LocationType.WAREHOUSE, 12.9716, 77.5946),
        ("Kolkata", LocationType.OUTLET, 22.5726, 88.3639),
        ("Hyderabad", LocationType.WAREHOUSE, 17.3850, 78.4867),
        ("Pune", LocationType.FACTORY, 18.5204, 73.8567),
        ("Ahmedabad", LocationType.OUTLET, 23.0225, 72.5714),
        ("Jaipur", LocationType.WAREHOUSE, 26.9124, 75.7873),
        ("Lucknow", LocationType.OUTLET, 26.8467, 80.9462),
    ]

    _ROUTE_DEFINITIONS: List[Tuple[str, str, float, float, float, float]] = [
        # (source, destination, distance_km, fuel_cost_inr, risk_factor, transit_hours)
        ("Mumbai", "Pune", 148.0, 4200.0, 0.12, 3.2),
        ("Mumbai", "Ahmedabad", 530.0, 14200.0, 0.18, 9.5),
        ("Mumbai", "Delhi", 1400.0, 38500.0, 0.22, 22.0),
        ("Pune", "Bengaluru", 840.0, 22800.0, 0.20, 14.5),
        ("Pune", "Hyderabad", 560.0, 15400.0, 0.17, 10.0),
        ("Ahmedabad", "Jaipur", 650.0, 17600.0, 0.16, 11.0),
        ("Ahmedabad", "Delhi", 950.0, 25800.0, 0.19, 15.5),
        ("Delhi", "Jaipur", 280.0, 7600.0, 0.11, 5.0),
        ("Delhi", "Lucknow", 550.0, 14800.0, 0.15, 9.0),
        ("Jaipur", "Lucknow", 570.0, 15200.0, 0.14, 9.5),
        ("Bengaluru", "Chennai", 350.0, 9200.0, 0.10, 6.5),
        ("Bengaluru", "Hyderabad", 570.0, 15100.0, 0.13, 9.0),
        ("Hyderabad", "Chennai", 630.0, 16800.0, 0.14, 10.5),
        ("Hyderabad", "Kolkata", 1200.0, 32000.0, 0.25, 20.0),
        ("Chennai", "Kolkata", 1350.0, 36200.0, 0.21, 21.0),
        ("Kolkata", "Lucknow", 980.0, 26500.0, 0.23, 18.0),
        ("Lucknow", "Delhi", 550.0, 14800.0, 0.15, 9.0),
        ("Mumbai", "Bengaluru", 980.0, 26800.0, 0.24, 17.0),
        ("Pune", "Ahmedabad", 660.0, 17800.0, 0.17, 11.5),
        ("Delhi", "Kolkata", 1470.0, 39500.0, 0.26, 23.0),
        ("Jaipur", "Ahmedabad", 650.0, 17600.0, 0.16, 11.0),
        ("Chennai", "Hyderabad", 630.0, 16800.0, 0.14, 10.5),
        ("Bengaluru", "Mumbai", 980.0, 27500.0, 0.24, 17.5),
        ("Kolkata", "Hyderabad", 1200.0, 32800.0, 0.25, 20.5),
    ]

    def __init__(self, seed: int = 42) -> None:
        """Initialize generator with optional random seed.

        Args:
            seed: Seed for any stochastic perturbations applied to routes.

        Time Complexity:
            O(1).

        Space Complexity:
            O(1).
        """
        self._random = random.Random(seed)

    def generate(self) -> Graph:
        """Create and return a fully populated supply chain graph.

        Returns:
            Connected ``Graph`` with 10 Indian hubs and directed routes.

        Time Complexity:
            O(V + E) — linear in nodes and edges inserted.

        Space Complexity:
            O(V + E) for graph storage.
        """
        graph = Graph()

        for name, loc_type, lat, lon in self._HUB_DEFINITIONS:
            graph.add_location(
                Location(
                    name=name,
                    location_type=loc_type,
                    latitude=lat,
                    longitude=lon,
                )
            )

        for source, dest, dist, cost, risk, hours in self._ROUTE_DEFINITIONS:
            perturbed = self._apply_variation(dist, cost, risk, hours)
            graph.add_route(
                source=source,
                destination=dest,
                distance_km=perturbed[0],
                fuel_cost_inr=perturbed[1],
                risk_factor=perturbed[2],
                transit_hours=perturbed[3],
            )

        return graph

    def _apply_variation(
        self,
        distance_km: float,
        fuel_cost_inr: float,
        risk_factor: float,
        transit_hours: float,
    ) -> Tuple[float, float, float, float]:
        """Apply small random perturbations to base route attributes.

        Simulates day-to-day variability in fuel prices, traffic, and delays.

        Time Complexity:
            O(1).

        Space Complexity:
            O(1).
        """
        distance_factor = self._random.uniform(0.97, 1.03)
        cost_factor = self._random.uniform(0.95, 1.08)
        risk_delta = self._random.uniform(-0.02, 0.03)
        hours_factor = self._random.uniform(0.96, 1.06)

        return (
            round(distance_km * distance_factor, 1),
            round(fuel_cost_inr * cost_factor, 2),
            round(min(1.0, max(0.0, risk_factor + risk_delta)), 3),
            round(transit_hours * hours_factor, 1),
        )

    @classmethod
    def hub_catalog(cls) -> List[str]:
        """Return ordered list of hub names in the mock network.

        Time Complexity:
            O(V).

        Space Complexity:
            O(V).
        """
        return [name for name, _, _, _ in cls._HUB_DEFINITIONS]

    @classmethod
    def describe_network(cls) -> str:
        """Return a human-readable summary of the mock topology.

        Time Complexity:
            O(V + E).

        Space Complexity:
            O(V + E) for output string.
        """
        lines = ["Mock Supply Chain Network (India)", "=" * 36]
        for name, loc_type, lat, lon in cls._HUB_DEFINITIONS:
            lines.append(f"  • {name} — {loc_type.value} ({lat}, {lon})")
        lines.append(f"\nDirected routes: {len(cls._ROUTE_DEFINITIONS)}")
        return "\n".join(lines)
