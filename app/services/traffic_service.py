"""In-memory traffic simulation for virtual users and cloud requests."""

from collections import deque
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from random import randint, uniform
from threading import Lock

from config import Config
from app.repositories.event_repository import save_event
from app.repositories.metric_repository import save_metric
from app.services.autoscaling_service import auto_scaler
from app.services.load_balancer_service import load_balancer
from app.services.node_service import node_manager


@dataclass
class VirtualUser:
    """Represent one artificial user generating cloud requests."""

    id: int
    name: str
    load_profile: int
    request_interval: float
    requests_sent: int = 0
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    next_request_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    def to_dict(self):
        """Serialize the user for frontend monitoring."""

        return {
            "id": self.id,
            "name": self.name,
            "load_profile": self.load_profile,
            "request_interval": self.request_interval,
            "requests_sent": self.requests_sent,
            "created_at": self.created_at.isoformat(),
            "next_request_at": self.next_request_at.isoformat(),
        }


@dataclass
class SimulatedRequest:
    """Track one active request until its simulated processing finishes."""

    id: int
    user_id: int
    node_id: int
    load_cost: int
    started_at: datetime
    ends_at: datetime

    def to_dict(self):
        """Serialize the active request for dashboard/API responses."""

        now = datetime.now(timezone.utc)
        remaining_ms = max(int((self.ends_at - now).total_seconds() * 1000), 0)

        return {
            "id": self.id,
            "user_id": self.user_id,
            "node_id": self.node_id,
            "load_cost": self.load_cost,
            "started_at": self.started_at.isoformat(),
            "ends_at": self.ends_at.isoformat(),
            "remaining_ms": remaining_ms,
        }


class TrafficSimulator:
    """Generate virtual users, requests, events and chart history."""

    def __init__(self):
        self._lock = Lock()
        self._users = {}
        self._active_requests = {}
        self._events = deque(maxlen=12)
        self._history = deque(maxlen=Config.METRICS_HISTORY_LIMIT)
        self._next_user_id = 1
        self._next_request_id = 1
        self.running = False

    def generate_users(self, count):
        """Create virtual users and immediately send an initial traffic burst."""

        normalized_count = self._normalize_user_count(count)

        with self._lock:
            self._advance_unlocked()
            created_users = []

            for _ in range(normalized_count):
                user = self._create_user_unlocked()
                created_users.append(user)
                self._dispatch_request_unlocked(user, immediate=True)

            self.running = bool(self._users)
            self._add_event_unlocked(
                "TRAFFIC_BURST",
                "INFO",
                f"Se generaron {normalized_count} usuarios virtuales y solicitudes iniciales.",
            )
            self._run_autoscaler_unlocked()
            self._sample_history_unlocked()

            return {
                "created_users": [user.to_dict() for user in created_users],
                "users": self.users_unlocked(),
                "active_requests": self.requests_unlocked(),
                "metrics": self.metrics_unlocked(),
            }

    def snapshot(self):
        """Advance the simulation and return dashboard-ready traffic state."""

        with self._lock:
            self._advance_unlocked()
            self._run_autoscaler_unlocked()
            self._sample_history_unlocked()

            return {
                "running": self.running,
                "traffic_mode": "virtual-users" if self.running else "idle",
                "autoscaling": auto_scaler.status(),
                "load_balancer": load_balancer.status(),
                "users": self.users_unlocked(),
                "requests": self.requests_unlocked(),
                "events": self.events_unlocked(),
                "charts": self.charts_unlocked(),
                "traffic_metrics": self.metrics_unlocked(),
            }

    def metrics_unlocked(self):
        """Return aggregate traffic metrics."""

        return {
            "virtual_users": len(self._users),
            "simulated_active_requests": len(self._active_requests),
        }

    def users_unlocked(self):
        """Serialize users while the lock is held."""

        return [self._users[user_id].to_dict() for user_id in sorted(self._users)]

    def requests_unlocked(self):
        """Serialize active simulated requests while the lock is held."""

        return [
            self._active_requests[request_id].to_dict()
            for request_id in sorted(self._active_requests)
        ]

    def events_unlocked(self):
        """Serialize recent traffic events while the lock is held."""

        return list(self._events)

    def charts_unlocked(self):
        """Return metric history formatted for Chart.js."""

        if not self._history:
            self._sample_history_unlocked()

        return {
            "labels": [entry["label"] for entry in self._history],
            "average_load": [entry["average_load"] for entry in self._history],
            "active_requests": [entry["active_requests"] for entry in self._history],
            "processed_requests": [entry["processed_requests"] for entry in self._history],
            "used_capacity": [entry["used_capacity"] for entry in self._history],
            "active_nodes": [entry["active_nodes"] for entry in self._history],
        }

    def _advance_unlocked(self):
        """Release finished requests and generate fresh requests for active users."""

        now = datetime.now(timezone.utc)
        self._release_finished_requests_unlocked(now)

        if not self._users:
            self.running = False
            return

        self.running = True

        for user in self._users.values():
            if now < user.next_request_at:
                continue

            self._dispatch_request_unlocked(user)
            jitter = uniform(0.65, 1.35)
            user.next_request_at = now + timedelta(seconds=user.request_interval * jitter)

    def _release_finished_requests_unlocked(self, now):
        """Complete active requests whose simulated processing time expired."""

        finished_ids = [
            request_id
            for request_id, simulated_request in self._active_requests.items()
            if simulated_request.ends_at <= now
        ]

        for request_id in finished_ids:
            simulated_request = self._active_requests.pop(request_id)

            try:
                node_manager.release_request(
                    simulated_request.node_id,
                    load_cost=simulated_request.load_cost,
                )
            except (KeyError, ValueError):
                self._add_event_unlocked(
                    "REQUEST_DROPPED",
                    "WARNING",
                    f"La solicitud {request_id} termino sin nodo disponible.",
                )

    def _dispatch_request_unlocked(self, user, immediate=False):
        """Assign a user request to the active node with the lowest current usage."""

        node = load_balancer.select_node()

        if node is None:
            self._add_event_unlocked(
                "REQUEST_REJECTED",
                "WARNING",
                "No hay capacidad activa disponible para recibir solicitudes.",
            )
            return None

        load_cost = max(user.load_profile + randint(-3, 6), 2)
        duration = uniform(4.5, 9.5)
        node, consumed_capacity = node_manager.assign_request(node.id, load_cost=load_cost)

        if consumed_capacity <= 0:
            return None

        request_id = self._next_request_id
        self._next_request_id += 1
        user.requests_sent += 1

        now = datetime.now(timezone.utc)
        simulated_request = SimulatedRequest(
            id=request_id,
            user_id=user.id,
            node_id=node.id,
            load_cost=consumed_capacity,
            started_at=now,
            ends_at=now + timedelta(seconds=duration),
        )
        self._active_requests[request_id] = simulated_request

        if immediate or request_id % 10 == 0:
            self._add_event_unlocked(
                "REQUEST_ASSIGNED",
                "INFO",
                f"Solicitud {request_id} asignada a {node.name} con costo {consumed_capacity}.",
            )

        return simulated_request

    def fail_node(self, node_id):
        """Simulate a node failure and redistribute its active requests."""

        with self._lock:
            node = node_manager.get_node(node_id)

            if node.failed:
                raise ValueError("Node already failed.")

            healthy_nodes = [
                candidate
                for candidate in node_manager.list_nodes()
                if candidate.active and not candidate.failed
            ]

            if len(healthy_nodes) <= 1:
                self._add_event_unlocked(
                    "FAILURE_PREVENTED",
                    "WARNING",
                    f"No se permite fallar {node.name}: se protege la disponibilidad minima.",
                )
                raise ValueError("Cannot fail the last available node.")

            moved_requests = self._drain_node_unlocked(node.id)

            if moved_requests is None:
                if node_manager.summary()["total_nodes"] < Config.MAX_NODE_COUNT:
                    replacement = node_manager.create_node()
                    self._add_event_unlocked(
                        "FAILOVER_CAPACITY_ADDED",
                        "WARNING",
                        f"{replacement.name} creado como capacidad de reemplazo para proteger alta disponibilidad.",
                    )
                    moved_requests = self._drain_node_unlocked(node.id)

                if moved_requests is None:
                    self._add_event_unlocked(
                        "FAILURE_PREVENTED",
                        "WARNING",
                        f"No hay capacidad suficiente para redistribuir la carga de {node.name}.",
                    )
                    raise ValueError("Not enough capacity to redistribute node workload.")

            failed_node = node_manager.fail_node(node.id)
            self._add_event_unlocked(
                "NODE_FAILED",
                "ERROR",
                f"{failed_node.name} fallo manualmente y salio del pool de balanceo.",
            )
            self._add_event_unlocked(
                "FAILOVER_COMPLETED",
                "INFO",
                f"{moved_requests} solicitudes reasignadas a nodos saludables.",
            )
            self._run_autoscaler_unlocked()
            self._sample_history_unlocked()

            return {
                "node": failed_node.to_dict(),
                "redistributed_requests": moved_requests,
                "load_balancer": load_balancer.status(),
                "metrics": node_manager.summary(),
            }

    def recover_node(self, node_id):
        """Recover a failed or inactive node and return it to the balancing pool."""

        with self._lock:
            node = node_manager.activate_node(node_id)
            self._add_event_unlocked(
                "NODE_RECOVERED",
                "INFO",
                f"{node.name} recuperado y disponible para nuevas solicitudes.",
            )
            self._rebalance_requests_unlocked()
            self._sample_history_unlocked()

            return {
                "node": node.to_dict(),
                "load_balancer": load_balancer.status(),
                "metrics": node_manager.summary(),
            }

    def _run_autoscaler_unlocked(self):
        """Let the autoscaler inspect load and mutate cloud capacity."""

        events = auto_scaler.evaluate(
            redistribute_callback=self._rebalance_requests_unlocked,
            drain_callback=self._drain_node_unlocked,
            simulation_running=self.running,
        )

        for event in events:
            self._add_event_unlocked(
                event["type"],
                event["severity"],
                event["description"],
            )

    def _rebalance_requests_unlocked(self):
        """Move active requests from hot nodes to cooler nodes after scaling."""

        moved_requests = 0
        max_moves_per_tick = 8

        while moved_requests < max_moves_per_tick:
            source = self._most_loaded_node_unlocked()
            target = self._least_loaded_node_unlocked(excluded_node_id=source.id if source else None)

            if source is None or target is None:
                break

            if source.usage_percentage - target.usage_percentage < 18:
                break

            request = self._request_for_node_unlocked(source.id)

            if request is None or target.current_load + request.load_cost > target.max_capacity:
                break

            node_manager.migrate_request(source.id, target.id, request.load_cost)
            request.node_id = target.id
            moved_requests += 1

        return moved_requests

    def _drain_node_unlocked(self, node_id):
        """Move requests away from a node before removing it."""

        moved_requests = 0
        requests_to_move = [
            request
            for request in self._active_requests.values()
            if request.node_id == node_id
        ]
        target_spare_capacity = sum(
            node.max_capacity - node.current_load
            for node in node_manager.list_nodes()
            if node.active and not node.failed and node.id != node_id
        )
        required_capacity = sum(request.load_cost for request in requests_to_move)

        if required_capacity > target_spare_capacity:
            return None

        for request in requests_to_move:
            target = self._least_loaded_node_unlocked(excluded_node_id=node_id)

            if target is None or target.current_load + request.load_cost > target.max_capacity:
                continue

            node_manager.migrate_request(node_id, target.id, request.load_cost)
            request.node_id = target.id
            moved_requests += 1

        has_remaining_requests = any(
            request.node_id == node_id for request in self._active_requests.values()
        )

        if has_remaining_requests:
            return None

        return moved_requests

    def _most_loaded_node_unlocked(self):
        candidates = [
            node
            for node in node_manager.list_nodes()
            if node.active and node.active_requests > 0
        ]

        if not candidates:
            return None

        return max(
            candidates,
            key=lambda node: (node.usage_percentage, node.active_requests, node.id),
        )

    def _least_loaded_node_unlocked(self, excluded_node_id=None):
        candidates = [
            node
            for node in node_manager.list_nodes()
            if (
                node.active
                and not node.failed
                and node.id != excluded_node_id
                and node.current_load < node.max_capacity
            )
        ]

        if not candidates:
            return None

        return min(
            candidates,
            key=lambda node: (node.usage_percentage, node.active_requests, node.id),
        )

    def _request_for_node_unlocked(self, node_id):
        requests = [
            request
            for request in self._active_requests.values()
            if request.node_id == node_id
        ]

        if not requests:
            return None

        return max(requests, key=lambda request: request.load_cost)

    def _create_user_unlocked(self):
        """Create one virtual user with a light randomized workload profile."""

        user_id = self._next_user_id
        self._next_user_id += 1
        now = datetime.now(timezone.utc)

        user = VirtualUser(
            id=user_id,
            name=f"User-{user_id:03d}",
            load_profile=randint(5, 14),
            request_interval=uniform(1.6, 3.8),
            created_at=now,
            next_request_at=now + timedelta(seconds=uniform(0.8, 2.2)),
        )
        self._users[user_id] = user

        return user

    def _sample_history_unlocked(self):
        """Append the current aggregate state to the chart history."""

        metrics = node_manager.summary()
        now = datetime.now(timezone.utc)
        label = now.strftime("%H:%M:%S")

        self._history.append(
            {
                "label": label,
                "average_load": metrics["average_load"],
                "active_requests": metrics["active_requests"],
                "processed_requests": metrics["processed_requests"],
                "used_capacity": metrics["used_capacity"],
                "active_nodes": metrics["active_nodes"],
            }
        )
        save_metric(now.isoformat(), metrics)

    def _add_event_unlocked(self, event_type, severity, description):
        """Add a recent dashboard event."""

        event = {
            "type": event_type,
            "severity": severity,
            "description": description,
            "created_at": datetime.now(timezone.utc).isoformat(),
        }
        self._events.appendleft(event)
        save_event(event)

    def _normalize_user_count(self, count):
        """Allow only the frontend traffic burst sizes requested for this stage."""

        try:
            normalized = int(count)
        except (TypeError, ValueError):
            normalized = 5

        return normalized if normalized in {5, 20, 50} else 5


traffic_simulator = TrafficSimulator()
