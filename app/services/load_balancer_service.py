"""Simplified load balancer used by the cloud traffic simulator."""

from app.services.node_service import node_manager


class LoadBalancer:
    """Select healthy nodes using a small cloud-style strategy."""

    def __init__(self, strategy="least_load"):
        self.strategy = strategy
        self._round_robin_index = 0
        self.last_target_node_id = None

    def select_node(self):
        """Return the next node that can receive requests."""

        candidates = self.available_nodes()

        if not candidates:
            self.last_target_node_id = None
            return None

        if self.strategy == "round_robin":
            node = candidates[self._round_robin_index % len(candidates)]
            self._round_robin_index += 1
        else:
            node = min(
                candidates,
                key=lambda candidate: (
                    candidate.usage_percentage,
                    candidate.active_requests,
                    candidate.id,
                ),
            )

        self.last_target_node_id = node.id
        return node

    def available_nodes(self):
        """Return healthy nodes with free capacity."""

        return [
            node
            for node in node_manager.list_nodes()
            if node.active and not node.failed and node.current_load < node.max_capacity
        ]

    def status(self):
        """Expose current balancing state for the dashboard."""

        return {
            "strategy": self.strategy,
            "available_nodes": len(self.available_nodes()),
            "last_target_node_id": self.last_target_node_id,
        }


load_balancer = LoadBalancer()
