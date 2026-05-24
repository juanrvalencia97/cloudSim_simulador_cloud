"""Shared repository helpers for SQLite access."""

import sqlite3

from config import Config


def get_connection():
    """Return a SQLite connection configured for dictionary-like rows."""

    connection = sqlite3.connect(Config.DATABASE_PATH)
    connection.row_factory = sqlite3.Row
    return connection
