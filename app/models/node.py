"""Domain model for simulated cloud nodes."""

from dataclasses import dataclass, field
from datetime import datetime, timezone


ACTIVE = "ACTIVE"
INACTIVE = "INACTIVE"
OVERLOADED = "OVERLOADED"
FAILED = "FAILED"


@dataclass
class Node:
    """Represent a virtual server inside the cloud simulator."""

    id: int
    name: str
    max_capacity: int
    active: bool = True
    failed: bool = False
    current_load: int = 0
    active_requests: int = 0
    processed_requests: int = 0
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    def activate(self):
        """Allow the node to receive simulated requests again."""

        self.active = True
        self.failed = False
        self._touch()

    def deactivate(self):
        """Stop the node and clear transient workload."""

        self.active = False
        self.failed = False
        self.current_load = 0
        self.active_requests = 0
        self._touch()

    def fail(self):
        """Mark the node as failed after its workload has been drained."""

        self.active = False
        self.failed = True
        self.current_load = 0
        self.active_requests = 0
        self._touch()

    def assign_request(self, load_cost):
        """Assign a simulated request and increase resource consumption."""

        if not self.active or self.failed:
            raise ValueError("Cannot assign requests to an inactive node.")

        normalized_cost = self._normalize_load_cost(load_cost)
        available_capacity = max(self.max_capacity - self.current_load, 0)
        consumed_capacity = min(normalized_cost, available_capacity)

        self.current_load += consumed_capacity
        self.active_requests += 1
        self._touch()

        return consumed_capacity

    def release_request(self, load_cost=None):
        """Release one simulated request and reduce resource consumption."""

        if self.active_requests <= 0:
            return 0

        normalized_cost = self._normalize_load_cost(load_cost or self.average_request_cost)
        released_capacity = min(normalized_cost, self.current_load)

        self.current_load -= released_capacity
        self.active_requests -= 1
        self.processed_requests += 1
        self._touch()

        return released_capacity

    def calculate_load_percentage(self):
        """Calculate current usage as a percentage of maximum capacity."""

        if self.max_capacity <= 0:
            return 0

        return round((self.current_load / self.max_capacity) * 100, 2)

    @property
    def usage_percentage(self):
        """Expose the current usage percentage."""

        return self.calculate_load_percentage()

    @property
    def uptime_seconds(self):
        """Return node uptime in seconds."""

        return int((datetime.now(timezone.utc) - self.created_at).total_seconds())

    @property
    def average_request_cost(self):
        """Estimate load to release when no explicit cost is provided."""

        if self.active_requests <= 0:
            return 0

        return max(round(self.current_load / self.active_requests), 1)

    @property
    def status(self):
        """Return the operational status used by the dashboard."""

        if self.failed:
            return FAILED

        if not self.active:
            return INACTIVE

        if self.usage_percentage >= 85:
            return OVERLOADED

        return ACTIVE

    def to_dict(self):
        """Serialize the node for JSON API responses."""

        return {
            "id": self.id,
            "name": self.name,
            "status": self.status,
            "active": self.active,
            "failed": self.failed,
            "usage_percentage": self.usage_percentage,
            "current_load": self.current_load,
            "max_capacity": self.max_capacity,
            "active_requests": self.active_requests,
            "processed_requests": self.processed_requests,
            "uptime_seconds": self.uptime_seconds,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
        }

    def _normalize_load_cost(self, load_cost):
        """Keep simulated resource costs inside a predictable range."""

        try:
            cost = int(load_cost)
        except (TypeError, ValueError):
            cost = 10

        return min(max(cost, 1), self.max_capacity)

    def _touch(self):
        self.updated_at = datetime.now(timezone.utc)
