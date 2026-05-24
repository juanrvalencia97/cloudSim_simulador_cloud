"""Automatic scaling policy for the cloud simulator."""

from config import Config
from app.services.node_service import node_manager


class AutoScaler:
    """Evaluate load and apply simplified cloud elasticity rules."""

    def __init__(
        self,
        min_nodes=Config.MIN_NODE_COUNT,
        max_nodes=Config.MAX_NODE_COUNT,
        scale_up_threshold=Config.SCALE_UP_THRESHOLD,
        scale_down_threshold=Config.SCALE_DOWN_THRESHOLD,
        scale_up_cycles=Config.SCALE_UP_CYCLES,
        scale_down_cycles=Config.SCALE_DOWN_CYCLES,
    ):
        self.min_nodes = min_nodes
        self.max_nodes = max_nodes
        self.scale_up_threshold = scale_up_threshold
        self.scale_down_threshold = scale_down_threshold
        self.scale_up_cycles = scale_up_cycles
        self.scale_down_cycles = scale_down_cycles
        self._high_load_cycles = 0
        self._low_load_cycles = 0
        self.enabled = True

    def evaluate(self, redistribute_callback, drain_callback, simulation_running=False):
        """Apply one autoscaling decision and return system events."""

        if not self.enabled or not simulation_running:
            self._reset_cycles()
            return []

        metrics = node_manager.summary()
        events = []

        self._track_load_cycles(metrics)

        if self._should_scale_up(metrics):
            node = node_manager.create_node()
            redistributed = redistribute_callback()
            self._reset_cycles()
            events.extend(
                [
                    self._event(
                        "HIGH_LOAD_DETECTED",
                        "WARNING",
                        f"Carga promedio de {metrics['average_load']}% supera el umbral de {self.scale_up_threshold}%.",
                    ),
                    self._event(
                        "NODE_CREATED",
                        "INFO",
                        f"{node.name} creado automaticamente para absorber trafico.",
                    ),
                ]
            )

            if redistributed:
                events.append(
                    self._event(
                        "REQUESTS_REDISTRIBUTED",
                        "INFO",
                        f"{redistributed} solicitudes redistribuidas hacia la nueva capacidad.",
                    )
                )

            return events

        if self._should_scale_down(metrics):
            node = self._select_removable_node(metrics["active_nodes"])

            if node is None:
                return events

            redistributed = drain_callback(node.id)

            if redistributed is None:
                return events

            deleted_node = node_manager.delete_node(node.id)
            self._reset_cycles()
            events.append(
                self._event(
                    "NODE_REMOVED",
                    "INFO",
                    f"{deleted_node.name} eliminado automaticamente por baja demanda.",
                )
            )

            if redistributed:
                events.append(
                    self._event(
                        "REQUESTS_REDISTRIBUTED",
                        "INFO",
                        f"{redistributed} solicitudes migradas antes de reducir capacidad.",
                    )
                )

        return events

    def status(self):
        """Return current autoscaling configuration for the dashboard."""

        return {
            "enabled": self.enabled,
            "min_nodes": self.min_nodes,
            "max_nodes": self.max_nodes,
            "scale_up_threshold": self.scale_up_threshold,
            "scale_down_threshold": self.scale_down_threshold,
            "scale_up_cycles": self.scale_up_cycles,
            "scale_down_cycles": self.scale_down_cycles,
            "high_load_cycles": self._high_load_cycles,
            "low_load_cycles": self._low_load_cycles,
        }

    def _should_scale_up(self, metrics):
        return (
            self._high_load_cycles >= self.scale_up_cycles
            and metrics["active_nodes"] < self.max_nodes
        )

    def _should_scale_down(self, metrics):
        return (
            self._low_load_cycles >= self.scale_down_cycles
            and metrics["active_nodes"] > self.min_nodes
        )

    def _track_load_cycles(self, metrics):
        if metrics["average_load"] > self.scale_up_threshold:
            self._high_load_cycles += 1
            self._low_load_cycles = 0
            return

        if metrics["average_load"] < self.scale_down_threshold:
            self._low_load_cycles += 1
            self._high_load_cycles = 0
            return

        self._reset_cycles()

    def _reset_cycles(self):
        self._high_load_cycles = 0
        self._low_load_cycles = 0

    def _select_removable_node(self, active_node_count):
        candidates = [
            node
            for node in node_manager.list_nodes()
            if node.active and active_node_count > self.min_nodes
        ]

        if not candidates:
            return None

        return min(
            candidates,
            key=lambda node: (node.active_requests, node.current_load, -node.id),
        )

    def _event(self, event_type, severity, description):
        return {
            "type": event_type,
            "severity": severity,
            "description": description,
        }


auto_scaler = AutoScaler()
