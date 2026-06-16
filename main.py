"""Interactive CLI for the Supply Chain Routing and Optimization Engine."""

from __future__ import annotations

import sys
from typing import List, Optional

from supply_chain.graph import Graph
from supply_chain.mock_data import MockDataGenerator
from supply_chain.router import DijkstraRouter, RouteResult, RoutingMetric


def _prompt_choice(prompt: str, options: List[str]) -> str:
    """Prompt user to select one option from a numbered list.

    Args:
        prompt: Display message before listing options.
        options: Valid choices shown with 1-based indexing.

    Returns:
        Selected option string.

    Time Complexity:
        O(n) per attempt where n is len(options) for validation.

    Space Complexity:
        O(1) beyond input storage.
    """
    print(prompt)
    for index, option in enumerate(options, start=1):
        print(f"  [{index}] {option}")

    while True:
        raw = input("\nEnter choice number: ").strip()
        if raw.isdigit():
            choice = int(raw)
            if 1 <= choice <= len(options):
                return options[choice - 1]
        print(f"Invalid choice. Please enter 1–{len(options)}.")


def _prompt_metric() -> RoutingMetric:
    """Prompt user to select a routing optimization metric.

    Returns:
        Selected ``RoutingMetric`` enum member.

    Time Complexity:
        O(1) — fixed number of options.

    Space Complexity:
        O(1).
    """
    labels = {
        "1": RoutingMetric.SHORTEST_DISTANCE,
        "2": RoutingMetric.LOWEST_COST,
        "3": RoutingMetric.BALANCED_EFFICIENCY,
    }
    print("\nSelect routing metric:")
    print("  [1] shortest_distance  — minimize total kilometers")
    print("  [2] lowest_cost        — minimize total fuel/toll cost (INR)")
    print("  [3] balanced_efficiency — weighted distance + cost + risk")

    while True:
        raw = input("\nEnter metric number: ").strip()
        if raw in labels:
            return labels[raw]
        print("Invalid choice. Please enter 1, 2, or 3.")


def _print_network_summary(graph: Graph) -> None:
    """Print overview of loaded supply chain network.

    Time Complexity:
        O(V).

    Space Complexity:
        O(1) auxiliary.
    """
    print("\n" + MockDataGenerator.describe_network())
    print(f"\nLoaded graph: {graph.vertex_count()} hubs, {graph.edge_count()} routes")


def _print_route_result(result: RouteResult, graph: Graph) -> None:
    """Pretty-print optimized route trajectory and complexity analysis.

    Args:
        result: Completed ``RouteResult`` from Dijkstra.
        graph: Source graph for location type lookups.

    Time Complexity:
        O(L) where L is path length for step printing.

    Space Complexity:
        O(1) auxiliary.
    """
    metric_label = result.metric.value.replace("_", " ").title()
    print("\n" + "=" * 60)
    print("  OPTIMIZED ROUTE RESULT")
    print("=" * 60)
    print(f"  Metric          : {metric_label}")
    print(f"  Source          : {result.source}")
    print(f"  Destination     : {result.destination}")
    print(f"  Hops            : {len(result.steps)}")
    print(f"  Optimized Weight: {result.optimized_weight:.4f}")

    print("\n  Step-by-Step Trajectory")
    print("  " + "-" * 56)
    for step_num, step in enumerate(result.steps, start=1):
        from_loc = graph.get_location(step.from_location)
        to_loc = graph.get_location(step.to_location)
        print(f"\n  Leg {step_num}: {step.from_location} → {step.to_location}")
        print(f"    From type     : {from_loc.location_type.value}")
        print(f"    To type       : {to_loc.location_type.value}")
        print(f"    Distance      : {step.distance_km:.1f} km")
        print(f"    Fuel cost     : ₹{step.fuel_cost_inr:,.2f}")
        print(f"    Risk factor   : {step.risk_factor:.3f}")
        print(f"    Transit time  : {step.transit_hours:.1f} hours")
        print(f"    Cumul. weight : {step.cumulative_weight:.4f}")

    print("\n  Route Summary")
    print("  " + "-" * 56)
    path_display = " → ".join(result.path)
    print(f"  Full path       : {path_display}")
    print(f"  Total distance  : {result.total_distance_km:.1f} km")
    print(f"  Total fuel cost : ₹{result.total_fuel_cost_inr:,.2f}")
    print(f"  Total transit   : {result.total_transit_hours:.1f} hours")
    print(f"  Max leg risk    : {result.max_risk_factor:.3f}")

    complexity = DijkstraRouter.complexity_analysis(
        graph.vertex_count(),
        graph.edge_count(),
    )
    print("\n  Time & Space Complexity Breakdown")
    print("  " + "-" * 56)
    print(f"  Algorithm       : {complexity['algorithm']}")
    print(f"  Time (Big-O)    : {complexity['time']}")
    print(f"  Space (Big-O)   : {complexity['space']}")
    print(f"  Heap insert     : {complexity['heap_insert']}")
    print(f"  Heap extract    : {complexity['heap_extract_min']}")
    print(f"  Path rebuild    : {complexity['path_reconstruction']}")
    print(f"  Relaxations     : {result.vertices_relaxations}")
    print(f"  Heap operations : {result.heap_operations}")
    print("=" * 60 + "\n")


def run_cli(graph: Optional[Graph] = None) -> None:
    """Execute the interactive supply chain routing CLI.

    Args:
        graph: Optional pre-built graph; generates mock data if omitted.

    Time Complexity:
        Dominated by single Dijkstra run: O((V + E) log V).

    Space Complexity:
        O(V + E) for graph plus O(V) for algorithm state.
    """
    if graph is None:
        generator = MockDataGenerator(seed=42)
        graph = generator.generate()

    _print_network_summary(graph)
    hubs = graph.location_names()
    router = DijkstraRouter(graph)

    print("\n--- Supply Chain Route Planner ---")
    source = _prompt_choice("\nSelect STARTING hub:", hubs)

    destination_options = [h for h in hubs if h != source]
    destination = _prompt_choice("\nSelect DESTINATION hub:", destination_options)

    if source == destination:
        print("Source and destination must differ.")
        return

    metric = _prompt_metric()

    try:
        result = router.find_route(source, destination, metric)
    except ValueError as exc:
        print(f"\nRouting failed: {exc}")
        return

    _print_route_result(result, graph)


def main() -> None:
    """Entry point for CLI execution.

    Time Complexity:
        O((V + E) log V) per routing query.

    Space Complexity:
        O(V + E).
    """
    try:
        run_cli()
    except KeyboardInterrupt:
        print("\n\nSession cancelled by user.")
        sys.exit(0)


if __name__ == "__main__":
    main()
