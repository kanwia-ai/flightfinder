"""Database connection and setup."""

import sqlite3
from pathlib import Path


class Database:
    """SQLite database connection manager."""

    def __init__(self, db_path: str):
        """Initialize database connection and create tables."""
        self.db_path = db_path

        # Create parent directories if needed
        if db_path != ":memory:":
            Path(db_path).parent.mkdir(parents=True, exist_ok=True)

        self.connection = sqlite3.connect(db_path)
        self.connection.row_factory = sqlite3.Row
        self._create_tables()

    def _create_tables(self):
        """Create database tables if they don't exist."""
        self.connection.executescript("""
            CREATE TABLE IF NOT EXISTS routes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                airline_code TEXT NOT NULL,
                origin TEXT NOT NULL,
                destination TEXT NOT NULL,
                last_updated TEXT NOT NULL,
                UNIQUE(airline_code, origin, destination)
            );

            CREATE TABLE IF NOT EXISTS searches (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT NOT NULL,
                origins TEXT NOT NULL,
                destination TEXT NOT NULL,
                depart_date TEXT NOT NULL,
                return_date TEXT,
                params_json TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS prices (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                search_id INTEGER,
                route TEXT NOT NULL,
                price REAL NOT NULL,
                booking_type TEXT NOT NULL,
                airline TEXT,
                fetched_at TEXT NOT NULL,
                FOREIGN KEY (search_id) REFERENCES searches(id)
            );

            CREATE INDEX IF NOT EXISTS idx_routes_origin ON routes(origin);
            CREATE INDEX IF NOT EXISTS idx_routes_destination ON routes(destination);
            CREATE INDEX IF NOT EXISTS idx_prices_route ON prices(route);
        """)
        self.connection.commit()

    def close(self):
        """Close the database connection."""
        self.connection.close()
