"""Route cache operations."""

from datetime import datetime

from flightfinder.db.database import Database


class RouteCache:
    """Manages the airline routes cache."""

    def __init__(self, db: Database):
        """Initialize with database connection."""
        self.db = db

    def add_route(self, airline_code: str, origin: str, destination: str):
        """Add a single route to the cache."""
        now = datetime.now().isoformat()
        self.db.connection.execute(
            """
            INSERT OR REPLACE INTO routes (airline_code, origin, destination, last_updated)
            VALUES (?, ?, ?, ?)
            """,
            (airline_code, origin.upper(), destination.upper(), now),
        )
        self.db.connection.commit()

    def add_routes(self, routes: list[tuple[str, str, str]]):
        """Add multiple routes to the cache."""
        now = datetime.now().isoformat()
        self.db.connection.executemany(
            """
            INSERT OR REPLACE INTO routes (airline_code, origin, destination, last_updated)
            VALUES (?, ?, ?, ?)
            """,
            [(code, orig.upper(), dest.upper(), now) for code, orig, dest in routes],
        )
        self.db.connection.commit()

    def get_routes_from(self, origin: str) -> list[dict]:
        """Get all routes departing from an airport."""
        cursor = self.db.connection.execute(
            "SELECT * FROM routes WHERE origin = ?",
            (origin.upper(),),
        )
        return [dict(row) for row in cursor.fetchall()]

    def get_destinations_from(self, origin: str) -> set[str]:
        """Get all destination airport codes from an origin."""
        cursor = self.db.connection.execute(
            "SELECT DISTINCT destination FROM routes WHERE origin = ?",
            (origin.upper(),),
        )
        return {row[0] for row in cursor.fetchall()}

    def clear(self):
        """Clear all routes from the cache."""
        self.db.connection.execute("DELETE FROM routes")
        self.db.connection.commit()

    def count(self) -> int:
        """Count total routes in cache."""
        cursor = self.db.connection.execute("SELECT COUNT(*) FROM routes")
        return cursor.fetchone()[0]
