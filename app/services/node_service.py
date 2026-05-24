"""Service responsible for managing simulated virtual nodes."""

from app.models.node import FAILED, INACTIVE, Node
from config import Config


class NodeManager:
    """Coordinate lifecycle and workload operations for virtual nodes."""

    def __init__(self, initial_nodes=0, default_capacity=100):
        self.default_capacity = default_capacity
        self._nodes = {}
        self._next_id = 1

        for _ in range(initial_nodes):
            self.create_node()

    def create_node(self, max_capacity=None):
        """Create and register a new active virtual node."""

        node_id = self._next_id
        self._next_id += 1

        node = Node(
            id=node_id,
            name=f"Node-{node_id}",
            max_capacity=max_capacity or self.default_capacity,
        )
        self._nodes[node_id] = node

        return node

    def delete_node(self, node_id):
        """Remove a node from the simulated infrastructure."""

        node = self._nodes.pop(int(node_id), None)

        if node is None:
            raise KeyError("Node not found.")

        return node

    def activate_node(self, node_id):
        """Activate an existing node."""

        node = self.get_node(node_id)
        node.activate()
        return node

    def deactivate_node(self, node_id):
        """Deactivate an existing node and clear its transient workload."""

        node = self.get_node(node_id)
        node.deactivate()
        return node

    def fail_node(self, node_id):
        """Mark an existing node as failed."""

        node = self.get_node(node_id)
        node.fail()
        return node

    def assign_request(self, node_id, load_cost=10):
        """Assign a request to a specific node."""

        node = self.get_node(node_id)
        consumed_capacity = node.assign_request(load_cost)
        return node, consumed_capacity

    def release_request(self, node_id, load_cost=None):
        """Release one active request from a specific node."""

        node = self.get_node(node_id)
        released_capacity = node.release_request(load_cost)
        return node, released_capacity

    def migrate_request(self, source_node_id, target_node_id, load_cost):
        """Move one active request between nodes without marking it processed."""

        source = self.get_node(source_node_id)
        target = self.get_node(target_node_id)

        if not target.active or target.failed:
            raise ValueError("Cannot migrate requests to an inactive node.")

        normalized_cost = max(int(load_cost), 1)

        if source.active_requests <= 0:
            raise ValueError("Source node has no active requests to migrate.")

        if target.current_load + normalized_cost > target.max_capacity:
            raise ValueError("Target node does not have enough capacity.")

        source.current_load = max(source.current_load - normalized_cost, 0)
        source.active_requests -= 1
        source._touch()

        target.current_load += normalized_cost
        target.active_requests += 1
        target._touch()

        return source, target

    def get_node(self, node_id):
        """Return a node by id or raise a clear error."""

        try:
            return self._nodes[int(node_id)]
        except (KeyError, ValueError):
            raise KeyError("Node not found.")

    def list_nodes(self):
        """Return all nodes ordered by creation id."""

        return [self._nodes[node_id] for node_id in sorted(self._nodes)]

    def summary(self):
        """Calculate aggregate metrics for all virtual nodes."""

        nodes = self.list_nodes()
        active_nodes = [node for node in nodes if node.active and not node.failed]
        inactive_nodes = [node for node in nodes if node.status == INACTIVE]
        failed_nodes = [node for node in nodes if node.status == FAILED]
        total_requests = sum(node.active_requests + node.processed_requests for node in nodes)
        processed_requests = sum(node.processed_requests for node in nodes)
        active_requests = sum(node.active_requests for node in nodes)
        total_capacity = sum(node.max_capacity for node in active_nodes)
        used_capacity = sum(node.current_load for node in active_nodes)
        average_load = round((used_capacity / total_capacity) * 100, 2) if total_capacity else 0
        availability = round((len(active_nodes) / len(nodes)) * 100, 2) if nodes else 0

        return {
            "total_nodes": len(nodes),
            "active_nodes": len(active_nodes),
            "inactive_nodes": len(inactive_nodes),
            "standby_nodes": 0,
            "failed_nodes": len(failed_nodes),
            "total_requests": total_requests,
            "processed_requests": processed_requests,
            "active_requests": active_requests,
            "failed_requests": 0,
            "total_capacity": total_capacity,
            "used_capacity": used_capacity,
            "average_load": average_load,
            "availability": availability,
        }

    def to_dict_list(self):
        """Serialize all nodes for API consumers."""

        return [node.to_dict() for node in self.list_nodes()]


node_manager = NodeManager(
    initial_nodes=Config.INITIAL_NODE_COUNT,
    default_capacity=Config.NODE_CAPACITY,
)
