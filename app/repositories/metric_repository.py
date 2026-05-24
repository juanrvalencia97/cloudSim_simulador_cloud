"""Persistence helpers for monitoring metrics."""

from app.repositories.base_repository import get_connection


def save_metric(timestamp, metrics):
    """Persist one monitoring sample in SQLite."""

    with get_connection() as connection:
        connection.execute(
            """
            INSERT INTO metrics (
                timestamp,
                average_load,
                active_nodes,
                failed_nodes,
                total_requests,
                processed_requests,
                failed_requests,
                total_capacity,
                used_capacity
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                timestamp,
                metrics["average_load"],
                metrics["active_nodes"],
                metrics["failed_nodes"],
                metrics["total_requests"],
                metrics["processed_requests"],
                metrics["failed_requests"],
                metrics["total_capacity"],
                metrics["used_capacity"],
            ),
        )
