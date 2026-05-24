"""SQLite schema initialization utilities."""

import sqlite3
from pathlib import Path


SCHEMA_STATEMENTS = [
    """
    CREATE TABLE IF NOT EXISTS nodes (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        status TEXT NOT NULL,
        current_load INTEGER NOT NULL DEFAULT 0,
        max_capacity INTEGER NOT NULL DEFAULT 100,
        processed_requests INTEGER NOT NULL DEFAULT 0,
        failed_requests INTEGER NOT NULL DEFAULT 0,
        created_at TEXT NOT NULL,
        updated_at TEXT NOT NULL
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS requests (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id TEXT NOT NULL,
        node_id INTEGER,
        status TEXT NOT NULL,
        load_cost INTEGER NOT NULL DEFAULT 0,
        created_at TEXT NOT NULL,
        processed_at TEXT,
        FOREIGN KEY (node_id) REFERENCES nodes (id)
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS metrics (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        timestamp TEXT NOT NULL,
        average_load REAL NOT NULL DEFAULT 0,
        active_nodes INTEGER NOT NULL DEFAULT 0,
        failed_nodes INTEGER NOT NULL DEFAULT 0,
        total_requests INTEGER NOT NULL DEFAULT 0,
        processed_requests INTEGER NOT NULL DEFAULT 0,
        failed_requests INTEGER NOT NULL DEFAULT 0,
        total_capacity INTEGER NOT NULL DEFAULT 0,
        used_capacity INTEGER NOT NULL DEFAULT 0
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS events (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        event_type TEXT NOT NULL,
        description TEXT NOT NULL,
        severity TEXT NOT NULL,
        created_at TEXT NOT NULL
    )
    """,
]

SCHEMA_MIGRATIONS = [
    "ALTER TABLE metrics ADD COLUMN total_capacity INTEGER NOT NULL DEFAULT 0",
    "ALTER TABLE metrics ADD COLUMN used_capacity INTEGER NOT NULL DEFAULT 0",
]


def init_database(database_path):
    """Create the SQLite database and base tables when needed."""

    path = Path(database_path)
    path.parent.mkdir(parents=True, exist_ok=True)

    with sqlite3.connect(path) as connection:
        for statement in SCHEMA_STATEMENTS:
            connection.execute(statement)
        for statement in SCHEMA_MIGRATIONS:
            try:
                connection.execute(statement)
            except sqlite3.OperationalError:
                pass
        connection.commit()
