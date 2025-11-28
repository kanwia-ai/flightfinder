"""Skiplagged (hidden city) route discovery."""

from flightfinder.db.routes import RouteCache


class SkiplaggedFinder:
    """Find skiplagged/hidden city ticketing opportunities."""

    def __init__(self, route_cache: RouteCache):
        """Initialize with route cache."""
        self.route_cache = route_cache

    def find_onward_destinations(self, destination: str) -> set[str]:
        """Find cities that flights continue to after the target destination.

        These are potential "book to X but get off at destination" opportunities.
        """
        return self.route_cache.get_destinations_from(destination)

    def build_skiplagged_targets(
        self, origin: str, intended_destination: str
    ) -> list[dict]:
        """Build list of search targets for skiplagged discovery.

        Returns searches to execute: origin -> onward_destination
        where onward flights pass through intended_destination.
        """
        onward_destinations = self.find_onward_destinations(intended_destination)

        return [
            {
                "origin": origin,
                "destination": dest,
                "intended_destination": intended_destination,
            }
            for dest in onward_destinations
        ]

    def is_skiplagged_connection(
        self, connection_airports: list[str], intended_destination: str
    ) -> bool:
        """Check if a flight route connects through the intended destination.

        Args:
            connection_airports: List of airport codes in order (origin, connections, final)
            intended_destination: Where we actually want to go

        Returns:
            True if intended_destination is a connection (not origin or final destination)
        """
        if len(connection_airports) < 2:
            return False

        # Check if intended destination is in the middle (not first or last)
        middle_stops = connection_airports[1:-1]
        return intended_destination.upper() in [s.upper() for s in middle_stops]
