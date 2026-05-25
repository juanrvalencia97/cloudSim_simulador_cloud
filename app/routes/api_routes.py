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

@api_bp.post("/reset")
def reset_simulation():
    """Reinicia toda la simulación al estado inicial."""
    from app.services.traffic_service import traffic_simulator
    from app.services.node_service import node_manager
    from app.services.load_balancer_service import load_balancer
    from app.services.autoscaling_service import auto_scaler
    from config import Config

    # Limpiar tráfico
    with traffic_simulator._lock:
        traffic_simulator._users.clear()
        traffic_simulator._active_requests.clear()
        traffic_simulator._events.clear()
        traffic_simulator._history.clear()
        traffic_simulator._next_user_id = 1
        traffic_simulator._next_request_id = 1
        traffic_simulator.running = False

    # Limpiar nodos y recrear los iniciales
    node_manager._nodes.clear()
    node_manager._next_id = 1
    for _ in range(Config.INITIAL_NODE_COUNT):
        node_manager.create_node()

    # Resetear balanceador
    load_balancer._round_robin_index = 0
    load_balancer.last_target_node_id = None

    # Resetear autoescalador
    auto_scaler._high_load_cycles = 0
    auto_scaler._low_load_cycles = 0

    return jsonify({"status": "reset", "message": "Simulación reiniciada correctamente."})

@api_bp.post("/traffic/pause")
def toggle_pause():
    """Pausa o reanuda la generación de tráfico."""
    from app.services.traffic_service import traffic_simulator
    with traffic_simulator._lock:
        traffic_simulator.paused = not traffic_simulator.paused
    return jsonify({"paused": traffic_simulator.paused})

@api_bp.delete("/traffic/users")
def remove_users():
    """Elimina N usuarios virtuales de la simulación."""
    from app.services.traffic_service import traffic_simulator
    payload = request.get_json(silent=True) or {}
    count = int(payload.get("count", 1))

    with traffic_simulator._lock:
        # Toma los últimos N user_ids y los elimina
        ids_to_remove = list(traffic_simulator._users.keys())[-count:]
        for uid in ids_to_remove:
            traffic_simulator._users.pop(uid, None)
        traffic_simulator.running = bool(traffic_simulator._users)

    removed = len(ids_to_remove)
    return jsonify({
        "removed": removed,
        "remaining": len(traffic_simulator._users)
    })

@api_bp.post("/config")
def update_config():
    """Actualiza parámetros del simulador en caliente sin reiniciar."""
    from app.services.autoscaling_service import auto_scaler
    from app.services.load_balancer_service import load_balancer
    from app.services.node_service import node_manager
    payload = request.get_json(silent=True) or {}

    if "scale_up_threshold" in payload:
        auto_scaler.scale_up_threshold = int(payload["scale_up_threshold"])
    if "scale_down_threshold" in payload:
        auto_scaler.scale_down_threshold = int(payload["scale_down_threshold"])
    if "min_nodes" in payload:
        auto_scaler.min_nodes = int(payload["min_nodes"])
    if "max_nodes" in payload:
        auto_scaler.max_nodes = int(payload["max_nodes"])
    if "strategy" in payload:
        load_balancer.strategy = payload["strategy"]  # "least_load" o "round_robin"

    return jsonify({
        "scale_up_threshold": auto_scaler.scale_up_threshold,
        "scale_down_threshold": auto_scaler.scale_down_threshold,
        "min_nodes": auto_scaler.min_nodes,
        "max_nodes": auto_scaler.max_nodes,
        "strategy": load_balancer.strategy,
    })