"""Flask web application for the Supply Chain Routing and Optimization Engine."""

from __future__ import annotations

from typing import Any, Dict, List

from flask import Flask, jsonify, render_template, request

from supply_chain.graph import Graph
from supply_chain.mock_data import MockDataGenerator
from supply_chain.router import DijkstraRouter, RouteResult, RoutingMetric

app = Flask(__name__)

# Load mock network once at startup — O(V + E) time, O(V + E) space.
GRAPH: Graph = MockDataGenerator(seed=42).generate()
ROUTER = DijkstraRouter(GRAPH)

METRIC_OPTIONS: List[Dict[str, str]] = [
    {
        "value": RoutingMetric.SHORTEST_DISTANCE.value,
        "label": "Shortest Distance",
        "description": "Minimize total kilometers traveled",
    },
    {
        "value": RoutingMetric.LOWEST_COST.value,
        "label": "Lowest Cost",
        "description": "Minimize fuel and toll expenses (INR)",
    },
    {
        "value": RoutingMetric.BALANCED_EFFICIENCY.value,
        "label": "Balanced Efficiency",
        "description": "Weighted blend of distance, cost, and risk",
    },
]

METRIC_LOOKUP = {metric["value"]: RoutingMetric(metric["value"]) for metric in METRIC_OPTIONS}


def _serialize_hubs() -> List[Dict[str, Any]]:
    """Return hub metadata for dropdown population.

    Time Complexity:
        O(V).

    Space Complexity:
        O(V).
    """
    hubs: List[Dict[str, Any]] = []
    for name in GRAPH.location_names():
        location = GRAPH.get_location(name)
        hubs.append(
            {
                "name": location.name,
                "type": location.location_type.value,
                "latitude": location.latitude,
                "longitude": location.longitude,
            }
        )
    return hubs


def _serialize_route_result(result: RouteResult) -> Dict[str, Any]:
    """Convert a RouteResult dataclass into JSON-serializable dict.

    Time Complexity:
        O(L) where L is path length.

    Space Complexity:
        O(L).
    """
    complexity = DijkstraRouter.complexity_analysis(
        GRAPH.vertex_count(),
        GRAPH.edge_count(),
    )

    steps: List[Dict[str, Any]] = []
    for index, step in enumerate(result.steps, start=1):
        from_loc = GRAPH.get_location(step.from_location)
        to_loc = GRAPH.get_location(step.to_location)
        steps.append(
            {
                "leg": index,
                "from": step.from_location,
                "to": step.to_location,
                "from_type": from_loc.location_type.value,
                "to_type": to_loc.location_type.value,
                "distance_km": round(step.distance_km, 1),
                "fuel_cost_inr": round(step.fuel_cost_inr, 2),
                "risk_factor": round(step.risk_factor, 3),
                "transit_hours": round(step.transit_hours, 1),
                "cumulative_weight": round(step.cumulative_weight, 4),
            }
        )

    return {
        "source": result.source,
        "destination": result.destination,
        "metric": result.metric.value,
        "metric_label": result.metric.value.replace("_", " ").title(),
        "path": result.path,
        "path_display": " → ".join(result.path),
        "steps": steps,
        "summary": {
            "total_distance_km": round(result.total_distance_km, 1),
            "total_fuel_cost_inr": round(result.total_fuel_cost_inr, 2),
            "total_transit_hours": round(result.total_transit_hours, 1),
            "max_risk_factor": round(result.max_risk_factor, 3),
            "optimized_weight": round(result.optimized_weight, 4),
            "hops": len(result.steps),
        },
        "complexity": {
            **complexity,
            "relaxations": result.vertices_relaxations,
            "heap_operations": result.heap_operations,
        },
        "network": {
            "vertices": GRAPH.vertex_count(),
            "edges": GRAPH.edge_count(),
        },
    }


@app.route("/")
def index() -> str:
    """Render the supply chain routing dashboard.

    Time Complexity:
        O(V) to serialize hub list.

    Space Complexity:
        O(V) for template context.
    """
    return render_template(
        "index.html",
        hubs=_serialize_hubs(),
        metrics=METRIC_OPTIONS,
        network={
            "vertices": GRAPH.vertex_count(),
            "edges": GRAPH.edge_count(),
        },
    )


@app.route("/api/hubs", methods=["GET"])
def api_hubs():
    """Return all supply chain hubs as JSON.

    Time Complexity:
        O(V).

    Space Complexity:
        O(V).
    """
    return jsonify({"hubs": _serialize_hubs()})


@app.route("/api/route", methods=["POST"])
def api_route():
    """Compute an optimized route using Dijkstra's algorithm.

    Expects JSON body:
        {
            "source": "Mumbai",
            "destination": "Kolkata",
            "metric": "shortest_distance"
        }

    Time Complexity:
        O((V + E) log V) per request.

    Space Complexity:
        O(V) auxiliary during search.
    """
    payload = request.get_json(silent=True) or {}

    source = (payload.get("source") or "").strip()
    destination = (payload.get("destination") or "").strip()
    metric_key = (payload.get("metric") or "").strip()

    if not source or not destination or not metric_key:
        return jsonify({"error": "source, destination, and metric are required."}), 400

    if source == destination:
        return jsonify({"error": "Source and destination must be different."}), 400

    if not GRAPH.has_location(source):
        return jsonify({"error": f"Unknown source hub: {source}"}), 400

    if not GRAPH.has_location(destination):
        return jsonify({"error": f"Unknown destination hub: {destination}"}), 400

    if metric_key not in METRIC_LOOKUP:
        return jsonify({"error": f"Unknown metric: {metric_key}"}), 400

    try:
        result = ROUTER.find_route(source, destination, METRIC_LOOKUP[metric_key])
    except ValueError as exc:
        return jsonify({"error": str(exc)}), 404

    return jsonify(_serialize_route_result(result))


@app.route("/api/network", methods=["GET"])
def api_network():
    """Return network statistics for the dashboard header.

    Time Complexity:
        O(1) — counts are cached on graph object.

    Space Complexity:
        O(1).
    """
    return jsonify(
        {
            "vertices": GRAPH.vertex_count(),
            "edges": GRAPH.edge_count(),
            "hubs": _serialize_hubs(),
        }
    )


if __name__ == "__main__":
    app.run(debug=True, host="127.0.0.1", port=5000)
