"""JSON API routes consumed by the frontend dashboard."""

from flask import Blueprint, jsonify, request

from app.services.dashboard_service import get_dashboard_status
from app.services.node_service import node_manager
from app.services.traffic_service import traffic_simulator


api_bp = Blueprint("api", __name__)


@api_bp.get("/health")
def health_check():
    """Return a simple health response for local and cloud checks."""

    return jsonify({"status": "ok", "service": "CloudSim API"})


@api_bp.get("/status")
def status():
    """Return the current simulator state used by the dashboard."""

    return jsonify(get_dashboard_status())


@api_bp.post("/traffic/users")
def generate_virtual_users():
    """Generate virtual users and an initial burst of simulated requests."""

    payload = request.get_json(silent=True) or {}
    traffic = traffic_simulator.generate_users(payload.get("count", 5))

    return jsonify({"traffic": traffic, "dashboard": get_dashboard_status()}), 201


@api_bp.get("/nodes")
def list_nodes():
    """Return all simulated virtual nodes."""

    return jsonify({"nodes": node_manager.to_dict_list(), "metrics": node_manager.summary()})


@api_bp.post("/nodes")
def create_node():
    """Create a virtual node with optional custom capacity."""

    payload = request.get_json(silent=True) or {}
    node = node_manager.create_node(max_capacity=payload.get("max_capacity"))
    return jsonify({"node": node.to_dict(), "metrics": node_manager.summary()}), 201


@api_bp.delete("/nodes/<int:node_id>")
def delete_node(node_id):
    """Delete a virtual node."""

    try:
        node = node_manager.delete_node(node_id)
    except KeyError:
        return jsonify({"error": "Node not found."}), 404

    return jsonify({"node": node.to_dict(), "metrics": node_manager.summary()})


@api_bp.post("/nodes/<int:node_id>/activate")
def activate_node(node_id):
    """Activate a virtual node."""

    try:
        node = node_manager.activate_node(node_id)
    except KeyError:
        return jsonify({"error": "Node not found."}), 404

    return jsonify({"node": node.to_dict(), "metrics": node_manager.summary()})


@api_bp.post("/nodes/<int:node_id>/deactivate")
def deactivate_node(node_id):
    """Deactivate a virtual node."""

    try:
        result = traffic_simulator.fail_node(node_id)
    except KeyError:
        return jsonify({"error": "Node not found."}), 404
    except ValueError as error:
        return jsonify({"error": str(error)}), 409

    return jsonify(result)


@api_bp.post("/nodes/<int:node_id>/recover")
def recover_node(node_id):
    """Recover a failed or inactive virtual node."""

    try:
        result = traffic_simulator.recover_node(node_id)
    except KeyError:
        return jsonify({"error": "Node not found."}), 404

    return jsonify(result)


@api_bp.post("/nodes/<int:node_id>/requests")
def assign_request(node_id):
    """Assign one simulated request to a node."""

    payload = request.get_json(silent=True) or {}

    try:
        node, consumed_capacity = node_manager.assign_request(
            node_id,
            load_cost=payload.get("load_cost", 10),
        )
    except KeyError:
        return jsonify({"error": "Node not found."}), 404
    except ValueError as error:
        return jsonify({"error": str(error)}), 409

    return jsonify(
        {
            "node": node.to_dict(),
            "consumed_capacity": consumed_capacity,
            "metrics": node_manager.summary(),
        }
    )


@api_bp.post("/nodes/<int:node_id>/release")
def release_request(node_id):
    """Release one simulated request from a node."""

    payload = request.get_json(silent=True) or {}

    try:
        node, released_capacity = node_manager.release_request(
            node_id,
            load_cost=payload.get("load_cost"),
        )
    except KeyError:
        return jsonify({"error": "Node not found."}), 404

    return jsonify(
        {
            "node": node.to_dict(),
            "released_capacity": released_capacity,
            "metrics": node_manager.summary(),
        }
    )
