"""Tests for route cache operations."""

import pytest

from flightfinder.db.database import Database
from flightfinder.db.routes import RouteCache


class TestRouteCache:
    """Tests for RouteCache class."""

    @pytest.fixture
    def db(self):
        """Create in-memory database for testing."""
        return Database(":memory:")

    @pytest.fixture
    def cache(self, db):
        """Create route cache with test database."""
        return RouteCache(db)

    def test_add_route(self, cache):
        """Test adding a single route."""
        cache.add_route("AF", "JFK", "CDG")
        routes = cache.get_routes_from("JFK")
        assert len(routes) == 1
        assert routes[0]["airline_code"] == "AF"
        assert routes[0]["destination"] == "CDG"

    def test_add_multiple_routes(self, cache):
        """Test adding multiple routes."""
        cache.add_routes([
            ("AF", "JFK", "CDG"),
            ("AF", "CDG", "YAO"),
            ("ET", "YAO", "ADD"),
        ])
        routes = cache.get_routes_from("CDG")
        assert len(routes) == 1
        assert routes[0]["destination"] == "YAO"

    def test_get_routes_from_airport(self, cache):
        """Test getting all routes from an airport."""
        cache.add_routes([
            ("AF", "YAO", "CDG"),
            ("ET", "YAO", "ADD"),
            ("RW", "YAO", "KGL"),
        ])
        routes = cache.get_routes_from("YAO")
        destinations = {r["destination"] for r in routes}
        assert destinations == {"CDG", "ADD", "KGL"}

    def test_get_destinations_from(self, cache):
        """Test getting just destination codes."""
        cache.add_routes([
            ("AF", "YAO", "CDG"),
            ("ET", "YAO", "ADD"),
        ])
        destinations = cache.get_destinations_from("YAO")
        assert destinations == {"CDG", "ADD"}

    def test_clear_routes(self, cache):
        """Test clearing all routes."""
        cache.add_route("AF", "JFK", "CDG")
        cache.clear()
        routes = cache.get_routes_from("JFK")
        assert len(routes) == 0

    def test_route_count(self, cache):
        """Test counting routes."""
        cache.add_routes([
            ("AF", "JFK", "CDG"),
            ("AF", "CDG", "YAO"),
        ])
        assert cache.count() == 2
