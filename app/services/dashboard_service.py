"""Dashboard state service."""

from datetime import datetime, timezone

from config import Config
from app.services.node_service import node_manager
from app.services.traffic_service import traffic_simulator


def get_dashboard_status():
    """Build the current dashboard payload for the frontend."""

    traffic = traffic_simulator.snapshot()
    nodes = node_manager.to_dict_list()
    metrics = node_manager.summary()
    metrics.update(traffic["traffic_metrics"])

    return {
        "app": {
            "name": Config.APP_NAME,
            "version": Config.API_VERSION,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        },
        "simulation": {
            "running": traffic["running"],
            "autoscaling_enabled": traffic["autoscaling"]["enabled"],
            "traffic_mode": traffic["traffic_mode"],
            "autoscaling": traffic["autoscaling"],
            "load_balancer": traffic["load_balancer"],
        },
        "metrics": metrics,
        "nodes": nodes,
        "users": traffic["users"],
        "requests": traffic["requests"],
        "charts": traffic["charts"],
        "events": [
            {
                "type": "SYSTEM_READY",
                "severity": "INFO",
                "description": "Dashboard inicial cargado correctamente.",
                "created_at": datetime.now(timezone.utc).isoformat(),
            }
        ]
        + traffic["events"],
    }
