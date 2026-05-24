"""Persistence helpers for simulator events."""

from app.repositories.base_repository import get_connection


def save_event(event):
    """Persist one important simulator event in SQLite."""

    with get_connection() as connection:
        connection.execute(
            """
            INSERT INTO events (event_type, description, severity, created_at)
            VALUES (?, ?, ?, ?)
            """,
            (
                event["type"],
                event["description"],
                event["severity"],
                event["created_at"],
            ),
        )


def get_recent_events(limit=30):
    """Return the latest persisted events."""

    with get_connection() as connection:
        rows = connection.execute(
            """
            SELECT event_type, description, severity, created_at
            FROM events
            ORDER BY id DESC
            LIMIT ?
            """,
            (limit,),
        ).fetchall()

    return [
        {
            "type": row["event_type"],
            "description": row["description"],
            "severity": row["severity"],
            "created_at": row["created_at"],
        }
        for row in rows
    ]
