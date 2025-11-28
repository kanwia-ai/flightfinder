"""Tests for skiplagged route discovery."""

import pytest

from flightfinder.db.database import Database
from flightfinder.db.routes import RouteCache
from flightfinder.skiplagged import SkiplaggedFinder


class TestSkiplaggedFinder:
    """Tests for skiplagged route discovery."""

    @pytest.fixture
    def db(self):
        """Create in-memory database."""
        return Database(":memory:")

    @pytest.fixture
    def route_cache(self, db):
        """Create route cache with test data."""
        cache = RouteCache(db)
        # Routes FROM Yaoundé (our target destination)
        cache.add_routes([
            ("AF", "YAO", "CDG"),  # Yaoundé to Paris
            ("ET", "YAO", "ADD"),  # Yaoundé to Addis Ababa
            ("RW", "YAO", "KGL"),  # Yaoundé to Kigali
            ("AF", "YAO", "LBV"),  # Yaoundé to Libreville
        ])
        return cache

    @pytest.fixture
    def finder(self, route_cache):
        """Create finder with test route cache."""
        return SkiplaggedFinder(route_cache)

    def test_find_onward_destinations(self, finder):
        """Test finding cities beyond target destination."""
        onward = finder.find_onward_destinations("YAO")

        assert "CDG" in onward
        assert "ADD" in onward
        assert "LBV" in onward
        assert len(onward) == 4

    def test_no_onward_destinations(self, finder):
        """Test when destination has no onward routes."""
        onward = finder.find_onward_destinations("XXX")

        assert len(onward) == 0

    def test_build_skiplagged_targets(self, finder):
        """Test building search targets for skiplagged discovery."""
        targets = finder.build_skiplagged_targets(
            origin="JFK",
            intended_destination="YAO",
        )

        # Should search JFK to each onward destination
        assert len(targets) == 4
        assert all(t["origin"] == "JFK" for t in targets)
        destinations = {t["destination"] for t in targets}
        assert destinations == {"CDG", "ADD", "KGL", "LBV"}

    def test_is_skiplagged_connection(self, finder):
        """Test checking if flight connects through target."""
        # Flight JFK -> CDG -> YAO -> LBV
        # If we want YAO, this is skiplagged (deplane at YAO)
        connections = ["JFK", "CDG", "YAO", "LBV"]

        assert finder.is_skiplagged_connection(connections, "YAO") is True
        assert finder.is_skiplagged_connection(connections, "CDG") is True
        assert finder.is_skiplagged_connection(connections, "LBV") is False  # Final dest
        assert finder.is_skiplagged_connection(connections, "JFK") is False  # Origin
