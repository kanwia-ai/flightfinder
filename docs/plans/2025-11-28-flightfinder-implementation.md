# FlightFinder Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Build a CLI flight search tool that finds cheapest flights from multiple origins with skiplagged discovery and n8n monitoring.

**Architecture:** Python CLI using Click for commands, httpx for async API calls, SQLite for caching routes/prices, Rich for terminal output. SerpAPI provides Google Flights data.

**Tech Stack:** Python 3.11+, Click, Rich, httpx, SQLite3, pytest

---

## Task 1: Config Module

**Files:**
- Create: `flightfinder/config.py`
- Test: `tests/test_config.py`

**Step 1: Write the failing test**

```python
# tests/test_config.py
"""Tests for configuration loading."""

import os
from pathlib import Path
from unittest.mock import patch

import pytest

from flightfinder.config import Config, get_config


class TestConfig:
    """Tests for Config class."""

    def test_config_from_env_var(self):
        """Test loading API key from environment variable."""
        with patch.dict(os.environ, {"FLIGHTFINDER_SERPAPI_KEY": "test-key-123"}):
            config = Config()
            assert config.serpapi_key == "test-key-123"

    def test_config_missing_key_returns_none(self):
        """Test missing API key returns None."""
        with patch.dict(os.environ, {}, clear=True):
            config = Config()
            assert config.serpapi_key is None

    def test_default_database_path(self):
        """Test default database path is set."""
        config = Config()
        assert config.database_path.name == "flights.db"
        assert ".local/share/flightfinder" in str(config.database_path)

    def test_default_cache_ttl(self):
        """Test default cache TTL is 6 hours."""
        config = Config()
        assert config.cache_ttl_seconds == 21600  # 6 hours

    def test_get_config_singleton(self):
        """Test get_config returns same instance."""
        config1 = get_config()
        config2 = get_config()
        assert config1 is config2
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/test_config.py -v`
Expected: FAIL with "ModuleNotFoundError: No module named 'flightfinder.config'"

**Step 3: Write minimal implementation**

```python
# flightfinder/config.py
"""Configuration loading for FlightFinder."""

import os
from dataclasses import dataclass, field
from pathlib import Path

_config_instance: "Config | None" = None


@dataclass
class Config:
    """Application configuration."""

    serpapi_key: str | None = field(default=None)
    database_path: Path = field(default_factory=lambda: Path.home() / ".local/share/flightfinder/flights.db")
    cache_ttl_seconds: int = 21600  # 6 hours
    api_delay_ms: int = 200
    max_retries: int = 3

    def __post_init__(self):
        """Load values from environment."""
        if self.serpapi_key is None:
            self.serpapi_key = os.environ.get("FLIGHTFINDER_SERPAPI_KEY")


def get_config() -> Config:
    """Get the global config instance (singleton)."""
    global _config_instance
    if _config_instance is None:
        _config_instance = Config()
    return _config_instance
```

**Step 4: Run test to verify it passes**

Run: `pytest tests/test_config.py -v`
Expected: PASS

**Step 5: Commit**

```bash
git add flightfinder/config.py tests/test_config.py
git commit -m "feat(config): add configuration loading from environment"
```

---

## Task 2: Database Connection

**Files:**
- Create: `flightfinder/db/database.py`
- Test: `tests/test_database.py`

**Step 1: Write the failing test**

```python
# tests/test_database.py
"""Tests for database connection and setup."""

import sqlite3
from pathlib import Path

import pytest

from flightfinder.db.database import Database


class TestDatabase:
    """Tests for Database class."""

    def test_create_database_in_memory(self):
        """Test creating in-memory database."""
        db = Database(":memory:")
        assert db.connection is not None

    def test_create_tables(self, tmp_path: Path):
        """Test tables are created on init."""
        db_path = tmp_path / "test.db"
        db = Database(str(db_path))

        # Check tables exist
        cursor = db.connection.execute(
            "SELECT name FROM sqlite_master WHERE type='table'"
        )
        tables = {row[0] for row in cursor.fetchall()}

        assert "routes" in tables
        assert "searches" in tables
        assert "prices" in tables

    def test_routes_table_schema(self, tmp_path: Path):
        """Test routes table has correct columns."""
        db_path = tmp_path / "test.db"
        db = Database(str(db_path))

        cursor = db.connection.execute("PRAGMA table_info(routes)")
        columns = {row[1] for row in cursor.fetchall()}

        assert "airline_code" in columns
        assert "origin" in columns
        assert "destination" in columns
        assert "last_updated" in columns

    def test_close_connection(self):
        """Test closing database connection."""
        db = Database(":memory:")
        db.close()
        with pytest.raises(sqlite3.ProgrammingError):
            db.connection.execute("SELECT 1")
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/test_database.py -v`
Expected: FAIL with "ModuleNotFoundError"

**Step 3: Write minimal implementation**

```python
# flightfinder/db/database.py
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
```

**Step 4: Run test to verify it passes**

Run: `pytest tests/test_database.py -v`
Expected: PASS

**Step 5: Commit**

```bash
git add flightfinder/db/database.py tests/test_database.py
git commit -m "feat(db): add database connection and table creation"
```

---

## Task 3: Route Cache Operations

**Files:**
- Create: `flightfinder/db/routes.py`
- Test: `tests/test_routes.py`

**Step 1: Write the failing test**

```python
# tests/test_routes.py
"""Tests for route cache operations."""

from datetime import datetime

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
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/test_routes.py -v`
Expected: FAIL with "ModuleNotFoundError"

**Step 3: Write minimal implementation**

```python
# flightfinder/db/routes.py
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
```

**Step 4: Run test to verify it passes**

Run: `pytest tests/test_routes.py -v`
Expected: PASS

**Step 5: Commit**

```bash
git add flightfinder/db/routes.py tests/test_routes.py
git commit -m "feat(db): add route cache operations"
```

---

## Task 4: SerpAPI Client

**Files:**
- Create: `flightfinder/api/serpapi.py`
- Create: `tests/fixtures/serpapi_response.json`
- Test: `tests/test_serpapi.py`

**Step 1: Create test fixture**

```json
// tests/fixtures/serpapi_response.json
{
  "best_flights": [
    {
      "flights": [
        {
          "departure_airport": {"id": "JFK", "name": "John F. Kennedy International Airport"},
          "arrival_airport": {"id": "CDG", "name": "Paris Charles de Gaulle Airport"},
          "airline": "Air France",
          "airline_logo": "https://...",
          "flight_number": "AF 007",
          "departure": {"time": "18:30", "date": "2025-03-15"},
          "arrival": {"time": "08:15", "date": "2025-03-16"},
          "duration": 465,
          "airplane": "Boeing 777"
        },
        {
          "departure_airport": {"id": "CDG", "name": "Paris Charles de Gaulle Airport"},
          "arrival_airport": {"id": "YAO", "name": "Yaounde Nsimalen International"},
          "airline": "Air France",
          "flight_number": "AF 840",
          "departure": {"time": "10:30", "date": "2025-03-16"},
          "arrival": {"time": "17:45", "date": "2025-03-16"},
          "duration": 375
        }
      ],
      "total_duration": 960,
      "price": 1203,
      "type": "Round trip"
    }
  ],
  "other_flights": [],
  "search_metadata": {
    "google_flights_url": "https://www.google.com/travel/flights?..."
  }
}
```

**Step 2: Write the failing test**

```python
# tests/test_serpapi.py
"""Tests for SerpAPI client."""

import json
from pathlib import Path
from unittest.mock import AsyncMock, patch

import pytest

from flightfinder.api.serpapi import SerpAPIClient, SerpAPIError
from flightfinder.models import BookingType, FlightOption


class TestSerpAPIClient:
    """Tests for SerpAPI client."""

    @pytest.fixture
    def mock_response(self):
        """Load mock API response."""
        fixture_path = Path(__file__).parent / "fixtures" / "serpapi_response.json"
        with open(fixture_path) as f:
            return json.load(f)

    @pytest.fixture
    def client(self):
        """Create client with test API key."""
        return SerpAPIClient(api_key="test-key")

    def test_client_requires_api_key(self):
        """Test client raises error without API key."""
        with pytest.raises(ValueError, match="API key required"):
            SerpAPIClient(api_key=None)

    @pytest.mark.asyncio
    async def test_search_flights_returns_options(self, client, mock_response):
        """Test search returns FlightOption objects."""
        with patch.object(client, "_make_request", new_callable=AsyncMock) as mock:
            mock.return_value = mock_response

            results = await client.search_flights(
                origin="JFK",
                destination="YAO",
                departure_date="2025-03-15",
                return_date="2025-03-25",
            )

            assert len(results) > 0
            assert isinstance(results[0], FlightOption)

    @pytest.mark.asyncio
    async def test_search_parses_price(self, client, mock_response):
        """Test price is correctly parsed."""
        with patch.object(client, "_make_request", new_callable=AsyncMock) as mock:
            mock.return_value = mock_response

            results = await client.search_flights(
                origin="JFK",
                destination="YAO",
                departure_date="2025-03-15",
            )

            assert results[0].total_price == 1203.0

    @pytest.mark.asyncio
    async def test_search_parses_flight_legs(self, client, mock_response):
        """Test flight legs are correctly parsed."""
        with patch.object(client, "_make_request", new_callable=AsyncMock) as mock:
            mock.return_value = mock_response

            results = await client.search_flights(
                origin="JFK",
                destination="YAO",
                departure_date="2025-03-15",
            )

            legs = results[0].outbound_legs
            assert len(legs) == 2
            assert legs[0].origin == "JFK"
            assert legs[0].destination == "CDG"
            assert legs[1].origin == "CDG"
            assert legs[1].destination == "YAO"

    @pytest.mark.asyncio
    async def test_search_includes_booking_url(self, client, mock_response):
        """Test booking URL is included."""
        with patch.object(client, "_make_request", new_callable=AsyncMock) as mock:
            mock.return_value = mock_response

            results = await client.search_flights(
                origin="JFK",
                destination="YAO",
                departure_date="2025-03-15",
            )

            assert "google.com" in results[0].booking_url
```

**Step 3: Run test to verify it fails**

Run: `pytest tests/test_serpapi.py -v`
Expected: FAIL with "ModuleNotFoundError"

**Step 4: Write minimal implementation**

```python
# flightfinder/api/serpapi.py
"""SerpAPI client for Google Flights data."""

from datetime import datetime

import httpx

from flightfinder.models import BookingType, FlightLeg, FlightOption


class SerpAPIError(Exception):
    """Error from SerpAPI."""

    pass


class SerpAPIClient:
    """Client for SerpAPI Google Flights endpoint."""

    BASE_URL = "https://serpapi.com/search"

    def __init__(self, api_key: str | None):
        """Initialize client with API key."""
        if not api_key:
            raise ValueError("API key required")
        self.api_key = api_key

    async def search_flights(
        self,
        origin: str,
        destination: str,
        departure_date: str,
        return_date: str | None = None,
    ) -> list[FlightOption]:
        """Search for flights between airports."""
        params = {
            "engine": "google_flights",
            "departure_id": origin,
            "arrival_id": destination,
            "outbound_date": departure_date,
            "api_key": self.api_key,
        }
        if return_date:
            params["return_date"] = return_date
            params["type"] = "1"  # Round trip
        else:
            params["type"] = "2"  # One way

        response = await self._make_request(params)
        return self._parse_response(response, return_date is not None)

    async def _make_request(self, params: dict) -> dict:
        """Make HTTP request to SerpAPI."""
        async with httpx.AsyncClient() as client:
            response = await client.get(self.BASE_URL, params=params, timeout=30.0)
            if response.status_code != 200:
                raise SerpAPIError(f"API error: {response.status_code}")
            return response.json()

    def _parse_response(self, data: dict, is_round_trip: bool) -> list[FlightOption]:
        """Parse API response into FlightOption objects."""
        options = []
        all_flights = data.get("best_flights", []) + data.get("other_flights", [])
        booking_url = data.get("search_metadata", {}).get("google_flights_url", "")

        for flight_data in all_flights:
            legs = self._parse_legs(flight_data.get("flights", []))
            if not legs:
                continue

            option = FlightOption(
                outbound_legs=legs,
                return_legs=None,  # TODO: Parse return flights
                total_price=float(flight_data.get("price", 0)),
                currency="USD",
                booking_type=BookingType.ROUND_TRIP if is_round_trip else BookingType.ONE_WAY,
                booking_url=booking_url,
            )
            options.append(option)

        return options

    def _parse_legs(self, flights: list[dict]) -> list[FlightLeg]:
        """Parse flight segments into FlightLeg objects."""
        legs = []
        for flight in flights:
            dep = flight.get("departure", {})
            arr = flight.get("arrival", {})

            # Parse datetime
            dep_dt = self._parse_datetime(dep.get("date", ""), dep.get("time", ""))
            arr_dt = self._parse_datetime(arr.get("date", ""), arr.get("time", ""))

            leg = FlightLeg(
                origin=flight.get("departure_airport", {}).get("id", ""),
                destination=flight.get("arrival_airport", {}).get("id", ""),
                airline=flight.get("airline", ""),
                flight_number=flight.get("flight_number", ""),
                departure=dep_dt,
                arrival=arr_dt,
                duration_minutes=flight.get("duration", 0),
            )
            legs.append(leg)

        return legs

    def _parse_datetime(self, date_str: str, time_str: str) -> datetime:
        """Parse date and time strings into datetime."""
        try:
            return datetime.strptime(f"{date_str} {time_str}", "%Y-%m-%d %H:%M")
        except ValueError:
            return datetime.now()
```

**Step 5: Run test to verify it passes**

Run: `pytest tests/test_serpapi.py -v`
Expected: PASS

**Step 6: Commit**

```bash
git add flightfinder/api/serpapi.py tests/test_serpapi.py tests/fixtures/
git commit -m "feat(api): add SerpAPI client for Google Flights"
```

---

## Task 5: Search Orchestrator

**Files:**
- Create: `flightfinder/search.py`
- Test: `tests/test_search.py`

**Step 1: Write the failing test**

```python
# tests/test_search.py
"""Tests for search orchestrator."""

from unittest.mock import AsyncMock, MagicMock

import pytest

from flightfinder.models import BookingType, FlightOption, SearchParams
from flightfinder.search import SearchOrchestrator


class TestSearchOrchestrator:
    """Tests for SearchOrchestrator."""

    @pytest.fixture
    def mock_api_client(self):
        """Create mock API client."""
        client = MagicMock()
        client.search_flights = AsyncMock(return_value=[])
        return client

    @pytest.fixture
    def orchestrator(self, mock_api_client):
        """Create orchestrator with mock client."""
        return SearchOrchestrator(api_client=mock_api_client)

    def test_build_search_combinations_single_origin(self, orchestrator):
        """Test building search combinations for single origin."""
        params = SearchParams(
            origins=["JFK"],
            destination="YAO",
            depart_date="2025-03-15",
            return_date="2025-03-25",
        )
        combos = orchestrator._build_search_combinations(params)

        # Should have: round-trip, outbound one-way, return one-way
        assert len(combos) == 3

    def test_build_search_combinations_multiple_origins(self, orchestrator):
        """Test building search combinations for multiple origins."""
        params = SearchParams(
            origins=["JFK", "EWR", "IAD"],
            destination="YAO",
            depart_date="2025-03-15",
            return_date="2025-03-25",
        )
        combos = orchestrator._build_search_combinations(params)

        # 3 origins × 3 types = 9 combinations
        assert len(combos) == 9

    def test_build_search_combinations_one_way(self, orchestrator):
        """Test one-way search has fewer combinations."""
        params = SearchParams(
            origins=["JFK"],
            destination="YAO",
            depart_date="2025-03-15",
            return_date=None,
        )
        combos = orchestrator._build_search_combinations(params)

        # One-way only
        assert len(combos) == 1

    @pytest.mark.asyncio
    async def test_search_calls_api_for_each_combination(self, orchestrator, mock_api_client):
        """Test search makes API call for each combination."""
        params = SearchParams(
            origins=["JFK", "EWR"],
            destination="YAO",
            depart_date="2025-03-15",
            return_date="2025-03-25",
        )

        await orchestrator.search(params)

        # 2 origins × 3 types = 6 calls
        assert mock_api_client.search_flights.call_count == 6

    @pytest.mark.asyncio
    async def test_search_aggregates_results(self, orchestrator, mock_api_client):
        """Test search aggregates results from all combinations."""
        mock_option = FlightOption(
            outbound_legs=[],
            return_legs=None,
            total_price=1000.0,
            currency="USD",
            booking_type=BookingType.ROUND_TRIP,
            booking_url="https://example.com",
        )
        mock_api_client.search_flights.return_value = [mock_option]

        params = SearchParams(
            origins=["JFK"],
            destination="YAO",
            depart_date="2025-03-15",
            return_date="2025-03-25",
        )

        results = await orchestrator.search(params)

        # 3 combinations, each returns 1 result
        assert len(results) == 3
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/test_search.py -v`
Expected: FAIL with "ModuleNotFoundError"

**Step 3: Write minimal implementation**

```python
# flightfinder/search.py
"""Search orchestrator for flight searches."""

import asyncio
from dataclasses import dataclass

from flightfinder.api.serpapi import SerpAPIClient
from flightfinder.models import FlightOption, SearchParams


@dataclass
class SearchCombination:
    """A single search to execute."""

    origin: str
    destination: str
    depart_date: str
    return_date: str | None
    search_type: str  # "round_trip", "outbound_oneway", "return_oneway"


class SearchOrchestrator:
    """Orchestrates flight searches across multiple origins and booking types."""

    def __init__(self, api_client: SerpAPIClient):
        """Initialize with API client."""
        self.api_client = api_client

    async def search(self, params: SearchParams) -> list[FlightOption]:
        """Execute search across all combinations."""
        combinations = self._build_search_combinations(params)
        results = []

        for combo in combinations:
            try:
                options = await self.api_client.search_flights(
                    origin=combo.origin,
                    destination=combo.destination,
                    departure_date=combo.depart_date,
                    return_date=combo.return_date,
                )
                results.extend(options)
            except Exception:
                # Log error but continue with other searches
                pass

        return results

    def _build_search_combinations(self, params: SearchParams) -> list[SearchCombination]:
        """Build list of all search combinations to execute."""
        combinations = []

        for origin in params.origins:
            if params.return_date:
                # Round trip
                combinations.append(
                    SearchCombination(
                        origin=origin,
                        destination=params.destination,
                        depart_date=params.depart_date,
                        return_date=params.return_date,
                        search_type="round_trip",
                    )
                )
                # Outbound one-way (for two-oneways comparison)
                combinations.append(
                    SearchCombination(
                        origin=origin,
                        destination=params.destination,
                        depart_date=params.depart_date,
                        return_date=None,
                        search_type="outbound_oneway",
                    )
                )
                # Return one-way
                combinations.append(
                    SearchCombination(
                        origin=params.destination,
                        destination=origin,
                        depart_date=params.return_date,
                        return_date=None,
                        search_type="return_oneway",
                    )
                )
            else:
                # One-way only
                combinations.append(
                    SearchCombination(
                        origin=origin,
                        destination=params.destination,
                        depart_date=params.depart_date,
                        return_date=None,
                        search_type="oneway",
                    )
                )

        return combinations
```

**Step 4: Run test to verify it passes**

Run: `pytest tests/test_search.py -v`
Expected: PASS

**Step 5: Commit**

```bash
git add flightfinder/search.py tests/test_search.py
git commit -m "feat(search): add search orchestrator for multiple origins"
```

---

## Task 6: Price Comparison Engine

**Files:**
- Create: `flightfinder/compare.py`
- Test: `tests/test_compare.py`

**Step 1: Write the failing test**

```python
# tests/test_compare.py
"""Tests for price comparison engine."""

from datetime import datetime

import pytest

from flightfinder.compare import PriceComparator, combine_one_ways
from flightfinder.models import BookingType, FlightLeg, FlightOption


class TestPriceComparator:
    """Tests for PriceComparator."""

    @pytest.fixture
    def sample_options(self):
        """Create sample flight options."""
        leg = FlightLeg(
            origin="JFK",
            destination="YAO",
            airline="AF",
            flight_number="AF007",
            departure=datetime(2025, 3, 15, 18, 30),
            arrival=datetime(2025, 3, 16, 17, 45),
            duration_minutes=840,
        )
        return [
            FlightOption(
                outbound_legs=[leg],
                return_legs=None,
                total_price=1500.0,
                currency="USD",
                booking_type=BookingType.ROUND_TRIP,
                booking_url="https://example.com/1",
            ),
            FlightOption(
                outbound_legs=[leg],
                return_legs=None,
                total_price=1200.0,
                currency="USD",
                booking_type=BookingType.ROUND_TRIP,
                booking_url="https://example.com/2",
            ),
            FlightOption(
                outbound_legs=[leg],
                return_legs=None,
                total_price=1800.0,
                currency="USD",
                booking_type=BookingType.ROUND_TRIP,
                booking_url="https://example.com/3",
            ),
        ]

    def test_sort_by_price(self, sample_options):
        """Test sorting options by price."""
        comparator = PriceComparator()
        sorted_options = comparator.sort_by_price(sample_options)

        prices = [opt.total_price for opt in sorted_options]
        assert prices == [1200.0, 1500.0, 1800.0]

    def test_filter_by_max_price(self, sample_options):
        """Test filtering by maximum price."""
        comparator = PriceComparator()
        filtered = comparator.filter_by_price(sample_options, max_price=1400.0)

        assert len(filtered) == 1
        assert filtered[0].total_price == 1200.0

    def test_top_n_results(self, sample_options):
        """Test getting top N cheapest results."""
        comparator = PriceComparator()
        top = comparator.top_n(sample_options, n=2)

        assert len(top) == 2
        assert top[0].total_price == 1200.0
        assert top[1].total_price == 1500.0

    def test_filter_by_max_stops(self):
        """Test filtering by maximum stops."""
        leg1 = FlightLeg("JFK", "CDG", "AF", "AF1", datetime.now(), datetime.now(), 400)
        leg2 = FlightLeg("CDG", "YAO", "AF", "AF2", datetime.now(), datetime.now(), 300)

        options = [
            FlightOption([leg1, leg2], None, 1000, "USD", BookingType.ONE_WAY, "url1"),  # 1 stop
            FlightOption([leg1], None, 1100, "USD", BookingType.ONE_WAY, "url2"),  # 0 stops
        ]

        comparator = PriceComparator()
        filtered = comparator.filter_by_stops(options, max_stops=0)

        assert len(filtered) == 1
        assert filtered[0].total_stops_outbound == 0


class TestCombineOneWays:
    """Tests for combining one-way flights."""

    def test_combine_outbound_and_return(self):
        """Test combining two one-ways into pseudo-roundtrip."""
        outbound = FlightOption(
            outbound_legs=[FlightLeg("JFK", "YAO", "AF", "AF1", datetime.now(), datetime.now(), 400)],
            return_legs=None,
            total_price=600.0,
            currency="USD",
            booking_type=BookingType.ONE_WAY,
            booking_url="url1",
        )
        return_flight = FlightOption(
            outbound_legs=[FlightLeg("YAO", "JFK", "ET", "ET1", datetime.now(), datetime.now(), 450)],
            return_legs=None,
            total_price=550.0,
            currency="USD",
            booking_type=BookingType.ONE_WAY,
            booking_url="url2",
        )

        combined = combine_one_ways(outbound, return_flight)

        assert combined.total_price == 1150.0
        assert combined.booking_type == BookingType.TWO_ONE_WAYS
        assert len(combined.outbound_legs) == 1
        assert len(combined.return_legs) == 1
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/test_compare.py -v`
Expected: FAIL with "ModuleNotFoundError"

**Step 3: Write minimal implementation**

```python
# flightfinder/compare.py
"""Price comparison and ranking engine."""

from flightfinder.models import BookingType, FlightOption


class PriceComparator:
    """Compare and rank flight options by price."""

    def sort_by_price(self, options: list[FlightOption]) -> list[FlightOption]:
        """Sort options by total price, cheapest first."""
        return sorted(options, key=lambda opt: opt.total_price)

    def filter_by_price(
        self, options: list[FlightOption], max_price: float
    ) -> list[FlightOption]:
        """Filter options by maximum price."""
        return [opt for opt in options if opt.total_price <= max_price]

    def filter_by_stops(
        self, options: list[FlightOption], max_stops: int
    ) -> list[FlightOption]:
        """Filter options by maximum number of stops."""
        return [opt for opt in options if opt.total_stops_outbound <= max_stops]

    def top_n(self, options: list[FlightOption], n: int) -> list[FlightOption]:
        """Get the top N cheapest options."""
        sorted_options = self.sort_by_price(options)
        return sorted_options[:n]


def combine_one_ways(
    outbound: FlightOption, return_flight: FlightOption
) -> FlightOption:
    """Combine two one-way flights into a two-oneways option."""
    return FlightOption(
        outbound_legs=outbound.outbound_legs,
        return_legs=return_flight.outbound_legs,  # The "outbound" of return becomes our return legs
        total_price=outbound.total_price + return_flight.total_price,
        currency=outbound.currency,
        booking_type=BookingType.TWO_ONE_WAYS,
        booking_url=f"{outbound.booking_url}|{return_flight.booking_url}",
    )
```

**Step 4: Run test to verify it passes**

Run: `pytest tests/test_compare.py -v`
Expected: PASS

**Step 5: Commit**

```bash
git add flightfinder/compare.py tests/test_compare.py
git commit -m "feat(compare): add price comparison and ranking engine"
```

---

## Task 7: Skiplagged Route Discovery

**Files:**
- Create: `flightfinder/skiplagged.py`
- Test: `tests/test_skiplagged.py`

**Step 1: Write the failing test**

```python
# tests/test_skiplagged.py
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
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/test_skiplagged.py -v`
Expected: FAIL with "ModuleNotFoundError"

**Step 3: Write minimal implementation**

```python
# flightfinder/skiplagged.py
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
```

**Step 4: Run test to verify it passes**

Run: `pytest tests/test_skiplagged.py -v`
Expected: PASS

**Step 5: Commit**

```bash
git add flightfinder/skiplagged.py tests/test_skiplagged.py
git commit -m "feat(skiplagged): add hidden city route discovery"
```

---

## Task 8: Interactive Mode Prompts

**Files:**
- Create: `flightfinder/interactive.py`
- Test: `tests/test_interactive.py`

**Step 1: Write the failing test**

```python
# tests/test_interactive.py
"""Tests for interactive mode prompts."""

from unittest.mock import MagicMock, patch

import pytest

from flightfinder.interactive import InteractiveSearch
from flightfinder.models import CabinClass, SearchParams


class TestInteractiveSearch:
    """Tests for interactive search mode."""

    @pytest.fixture
    def interactive(self):
        """Create interactive search instance."""
        return InteractiveSearch()

    def test_parse_airports_single(self, interactive):
        """Test parsing single airport code."""
        result = interactive._parse_airports("JFK")
        assert result == ["JFK"]

    def test_parse_airports_multiple(self, interactive):
        """Test parsing multiple airport codes."""
        result = interactive._parse_airports("JFK, EWR, IAD")
        assert result == ["JFK", "EWR", "IAD"]

    def test_parse_airports_with_spaces(self, interactive):
        """Test parsing handles extra spaces."""
        result = interactive._parse_airports("  JFK ,  EWR  ")
        assert result == ["JFK", "EWR"]

    def test_parse_time_valid(self, interactive):
        """Test parsing valid time."""
        result = interactive._parse_time("18:30")
        assert result == "18:30"

    def test_parse_time_empty(self, interactive):
        """Test parsing empty time returns None."""
        result = interactive._parse_time("")
        assert result is None

    def test_parse_time_any(self, interactive):
        """Test parsing 'any' returns None."""
        result = interactive._parse_time("any")
        assert result is None

    def test_parse_duration_hours(self, interactive):
        """Test parsing duration in hours."""
        result = interactive._parse_duration("24h")
        assert result == 1440  # minutes

    def test_parse_duration_minutes(self, interactive):
        """Test parsing duration in minutes."""
        result = interactive._parse_duration("90m")
        assert result == 90

    def test_parse_cabin_class(self, interactive):
        """Test parsing cabin class."""
        assert interactive._parse_cabin("economy") == CabinClass.ECONOMY
        assert interactive._parse_cabin("business") == CabinClass.BUSINESS
        assert interactive._parse_cabin("") == CabinClass.ECONOMY  # default

    def test_build_params_from_responses(self, interactive):
        """Test building SearchParams from user responses."""
        responses = {
            "origins": "JFK, EWR",
            "destination": "YAO",
            "depart_date": "2025-03-15",
            "return_date": "2025-03-25",
            "depart_after": "18:00",
            "max_stops": "1",
            "cabin": "economy",
            "include_skiplagged": "y",
        }

        params = interactive._build_params(responses)

        assert isinstance(params, SearchParams)
        assert params.origins == ["JFK", "EWR"]
        assert params.destination == "YAO"
        assert params.depart_after == "18:00"
        assert params.max_stops == 1
        assert params.include_skiplagged is True
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/test_interactive.py -v`
Expected: FAIL with "ModuleNotFoundError"

**Step 3: Write minimal implementation**

```python
# flightfinder/interactive.py
"""Interactive mode prompts for flight search."""

import re

from rich.console import Console
from rich.prompt import Prompt

from flightfinder.models import CabinClass, SearchParams


class InteractiveSearch:
    """Interactive prompts for building search parameters."""

    def __init__(self):
        """Initialize with Rich console."""
        self.console = Console()

    def _parse_airports(self, value: str) -> list[str]:
        """Parse comma-separated airport codes."""
        return [code.strip().upper() for code in value.split(",") if code.strip()]

    def _parse_time(self, value: str) -> str | None:
        """Parse time value, return None for empty or 'any'."""
        value = value.strip().lower()
        if not value or value == "any":
            return None
        return value

    def _parse_duration(self, value: str) -> int | None:
        """Parse duration like '24h' or '90m' into minutes."""
        value = value.strip().lower()
        if not value or value == "any":
            return None

        match = re.match(r"(\d+)(h|m)", value)
        if not match:
            return None

        num, unit = match.groups()
        minutes = int(num)
        if unit == "h":
            minutes *= 60
        return minutes

    def _parse_cabin(self, value: str) -> CabinClass:
        """Parse cabin class string."""
        value = value.strip().lower()
        mapping = {
            "economy": CabinClass.ECONOMY,
            "premium": CabinClass.PREMIUM_ECONOMY,
            "business": CabinClass.BUSINESS,
            "first": CabinClass.FIRST,
        }
        return mapping.get(value, CabinClass.ECONOMY)

    def _parse_bool(self, value: str) -> bool:
        """Parse yes/no response."""
        return value.strip().lower() in ("y", "yes", "true", "1")

    def _parse_int(self, value: str) -> int | None:
        """Parse integer or return None."""
        value = value.strip()
        if not value or value.lower() == "any":
            return None
        try:
            return int(value)
        except ValueError:
            return None

    def _parse_float(self, value: str) -> float | None:
        """Parse float or return None."""
        value = value.strip()
        if not value or value.lower() == "any":
            return None
        try:
            return float(value)
        except ValueError:
            return None

    def _build_params(self, responses: dict) -> SearchParams:
        """Build SearchParams from user responses."""
        return SearchParams(
            origins=self._parse_airports(responses.get("origins", "")),
            destination=responses.get("destination", "").strip().upper(),
            depart_date=responses.get("depart_date", ""),
            return_date=responses.get("return_date") if responses.get("return_date", "").lower() != "oneway" else None,
            depart_after=self._parse_time(responses.get("depart_after", "")),
            depart_before=self._parse_time(responses.get("depart_before", "")),
            arrive_after=self._parse_time(responses.get("arrive_after", "")),
            arrive_before=self._parse_time(responses.get("arrive_before", "")),
            max_stops=self._parse_int(responses.get("max_stops", "")),
            max_duration_minutes=self._parse_duration(responses.get("max_duration", "")),
            cabin=self._parse_cabin(responses.get("cabin", "")),
            airlines_exclude=self._parse_airports(responses.get("airlines_avoid", "")),
            min_layover_minutes=self._parse_duration(responses.get("layover_min", "45m")) or 45,
            max_layover_minutes=self._parse_duration(responses.get("layover_max", "")),
            max_price=self._parse_float(responses.get("max_price", "")),
            alert_below=self._parse_float(responses.get("alert_below", "")),
            include_skiplagged=self._parse_bool(responses.get("include_skiplagged", "")),
            nearby_km=self._parse_int(responses.get("nearby_km", "")),
        )

    def run(self) -> SearchParams:
        """Run interactive prompts and return SearchParams."""
        self.console.print("\n[bold]FlightFinder Interactive Search[/bold]\n")

        responses = {}

        responses["origins"] = Prompt.ask("Origin airports (comma-separated)")
        responses["destination"] = Prompt.ask("Destination")
        responses["nearby_km"] = Prompt.ask("Search nearby airports within", default="skip")

        responses["depart_date"] = Prompt.ask("\nDeparture date (YYYY-MM-DD)")
        responses["flex_days"] = Prompt.ask("Flexible ± days", default="0")
        responses["depart_after"] = Prompt.ask("Depart after", default="any")
        responses["arrive_before"] = Prompt.ask("Arrive before", default="any")

        responses["return_date"] = Prompt.ask("\nReturn date (YYYY-MM-DD or 'oneway')")

        responses["max_stops"] = Prompt.ask("\nMax stops", default="any")
        responses["max_duration"] = Prompt.ask("Max travel time", default="any")
        responses["cabin"] = Prompt.ask("Cabin", default="economy")
        responses["airlines_avoid"] = Prompt.ask("Airlines to avoid", default="none")
        responses["layover_min"] = Prompt.ask("Layover min", default="45m")
        responses["layover_max"] = Prompt.ask("Layover max", default="any")

        responses["max_price"] = Prompt.ask("\nMax price", default="any")
        responses["alert_below"] = Prompt.ask("Alert if below", default="none")

        responses["include_skiplagged"] = Prompt.ask("\nInclude skiplagged fares?", default="n")

        return self._build_params(responses)
```

**Step 4: Run test to verify it passes**

Run: `pytest tests/test_interactive.py -v`
Expected: PASS

**Step 5: Commit**

```bash
git add flightfinder/interactive.py tests/test_interactive.py
git commit -m "feat(interactive): add interactive mode prompts"
```

---

## Task 9: Rich Output Formatter

**Files:**
- Create: `flightfinder/output.py`
- Test: `tests/test_output.py`

**Step 1: Write the failing test**

```python
# tests/test_output.py
"""Tests for Rich output formatting."""

from datetime import datetime
from io import StringIO

import pytest

from flightfinder.models import BookingType, FlightLeg, FlightOption
from flightfinder.output import OutputFormatter


class TestOutputFormatter:
    """Tests for output formatting."""

    @pytest.fixture
    def sample_option(self):
        """Create sample flight option."""
        outbound = FlightLeg(
            origin="JFK",
            destination="YAO",
            airline="Air France",
            flight_number="AF007",
            departure=datetime(2025, 3, 15, 18, 30),
            arrival=datetime(2025, 3, 16, 17, 45),
            duration_minutes=840,
        )
        return FlightOption(
            outbound_legs=[outbound],
            return_legs=None,
            total_price=1203.0,
            currency="USD",
            booking_type=BookingType.ROUND_TRIP,
            booking_url="https://google.com/flights/123",
        )

    @pytest.fixture
    def formatter(self):
        """Create formatter."""
        return OutputFormatter()

    def test_format_price(self, formatter):
        """Test price formatting."""
        assert formatter.format_price(1203.0, "USD") == "$1,203"
        assert formatter.format_price(999.99, "USD") == "$1,000"

    def test_format_duration(self, formatter):
        """Test duration formatting."""
        assert formatter.format_duration(90) == "1h 30m"
        assert formatter.format_duration(60) == "1h 0m"
        assert formatter.format_duration(45) == "0h 45m"

    def test_format_datetime(self, formatter):
        """Test datetime formatting."""
        dt = datetime(2025, 3, 15, 18, 30)
        assert formatter.format_time(dt) == "18:30"
        assert formatter.format_date(dt) == "Mar 15"

    def test_format_stops(self, formatter):
        """Test stops formatting."""
        assert formatter.format_stops(0) == "Direct"
        assert formatter.format_stops(1) == "1 stop"
        assert formatter.format_stops(2) == "2 stops"

    def test_build_results_table(self, formatter, sample_option):
        """Test building results table."""
        table = formatter.build_results_table([sample_option])
        # Table should have content
        assert table is not None

    def test_format_booking_type(self, formatter):
        """Test booking type formatting."""
        assert formatter.format_booking_type(BookingType.ROUND_TRIP) == "round-trip"
        assert formatter.format_booking_type(BookingType.SKIPLAGGED) == "skiplagged"
        assert formatter.format_booking_type(BookingType.TWO_ONE_WAYS) == "two-oneways"
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/test_output.py -v`
Expected: FAIL with "ModuleNotFoundError"

**Step 3: Write minimal implementation**

```python
# flightfinder/output.py
"""Rich terminal output formatting."""

from datetime import datetime

from rich.console import Console
from rich.table import Table

from flightfinder.models import BookingType, FlightOption


class OutputFormatter:
    """Format flight results for terminal output."""

    def __init__(self):
        """Initialize with Rich console."""
        self.console = Console()

    def format_price(self, price: float, currency: str) -> str:
        """Format price with currency symbol."""
        if currency == "USD":
            return f"${price:,.0f}"
        return f"{price:,.0f} {currency}"

    def format_duration(self, minutes: int) -> str:
        """Format duration in hours and minutes."""
        hours = minutes // 60
        mins = minutes % 60
        return f"{hours}h {mins}m"

    def format_time(self, dt: datetime) -> str:
        """Format time as HH:MM."""
        return dt.strftime("%H:%M")

    def format_date(self, dt: datetime) -> str:
        """Format date as Mon DD."""
        return dt.strftime("%b %d")

    def format_stops(self, stops: int) -> str:
        """Format number of stops."""
        if stops == 0:
            return "Direct"
        if stops == 1:
            return "1 stop"
        return f"{stops} stops"

    def format_booking_type(self, booking_type: BookingType) -> str:
        """Format booking type for display."""
        return booking_type.value

    def build_results_table(self, options: list[FlightOption]) -> Table:
        """Build Rich table with search results."""
        table = Table(title="Flight Results")

        table.add_column("#", justify="right", style="cyan")
        table.add_column("Price", justify="right", style="green")
        table.add_column("Type", style="yellow")
        table.add_column("Route")
        table.add_column("Outbound")
        table.add_column("Stops", justify="center")

        for i, option in enumerate(options, 1):
            # Build route string
            if option.outbound_legs:
                origin = option.outbound_legs[0].origin
                dest = option.outbound_legs[-1].destination
                route = f"{origin} → {dest}"
            else:
                route = "N/A"

            # Outbound timing
            if option.outbound_legs:
                dep = option.outbound_legs[0].departure
                outbound = f"{self.format_date(dep)} {self.format_time(dep)}"
            else:
                outbound = "N/A"

            table.add_row(
                str(i),
                self.format_price(option.total_price, option.currency),
                self.format_booking_type(option.booking_type),
                route,
                outbound,
                self.format_stops(option.total_stops_outbound),
            )

        return table

    def print_results(self, options: list[FlightOption]):
        """Print results table to console."""
        if not options:
            self.console.print("[yellow]No flights found matching your criteria.[/yellow]")
            return

        table = self.build_results_table(options)
        self.console.print(table)

    def print_detail(self, option: FlightOption, index: int):
        """Print detailed flight information."""
        self.console.print(f"\n[bold]FLIGHT #{index}[/bold] - {self.format_price(option.total_price, option.currency)} ({self.format_booking_type(option.booking_type)})")

        if option.is_skiplagged:
            self.console.print(f"\n[bold red]⚠️  SKIPLAGGED:[/bold red] Book to {option.skiplagged_deplane_at}, deplane early. No checked bags.")

        self.console.print("\n[bold]OUTBOUND[/bold]")
        for leg in option.outbound_legs:
            self.console.print(
                f"  {leg.origin} {self.format_time(leg.departure)} → "
                f"{leg.destination} {self.format_time(leg.arrival)} "
                f"({leg.airline} {leg.flight_number}) - {self.format_duration(leg.duration_minutes)}"
            )

        if option.return_legs:
            self.console.print("\n[bold]RETURN[/bold]")
            for leg in option.return_legs:
                self.console.print(
                    f"  {leg.origin} {self.format_time(leg.departure)} → "
                    f"{leg.destination} {self.format_time(leg.arrival)} "
                    f"({leg.airline} {leg.flight_number}) - {self.format_duration(leg.duration_minutes)}"
                )

        self.console.print(f"\n[dim]Booking: {option.booking_url}[/dim]")
```

**Step 4: Run test to verify it passes**

Run: `pytest tests/test_output.py -v`
Expected: PASS

**Step 5: Commit**

```bash
git add flightfinder/output.py tests/test_output.py
git commit -m "feat(output): add Rich terminal output formatting"
```

---

## Task 10: Wire Up CLI Commands

**Files:**
- Modify: `flightfinder/cli.py`
- Test: `tests/test_cli.py` (update existing)

**Step 1: Write the failing test**

```python
# Add to tests/test_cli.py

class TestQuickCommandIntegration:
    """Integration tests for quick command."""

    def test_quick_shows_searching_message(self):
        """Test quick command shows searching feedback."""
        runner = CliRunner()
        # Mock the API so we don't make real calls
        with patch("flightfinder.cli.get_config") as mock_config:
            mock_config.return_value.serpapi_key = None  # No API key
            result = runner.invoke(quick, ["JFK", "YAO", "2025-03-15", "2025-03-25"])
            # Should show error about missing API key
            assert "API key" in result.output or result.exit_code != 0


class TestSearchCommandIntegration:
    """Integration tests for search command."""

    def test_search_launches_interactive(self):
        """Test search command enters interactive mode."""
        runner = CliRunner()
        # Provide minimal input to interactive prompts
        result = runner.invoke(search, input="JFK\nYAO\nskip\n2025-03-15\n0\nany\nany\n2025-03-25\nany\nany\neconomy\nnone\n45m\nany\nany\nnone\nn\n")
        # Should process inputs without crashing
        assert result.exit_code == 0 or "API key" in result.output
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/test_cli.py::TestQuickCommandIntegration -v`
Expected: FAIL (current implementation doesn't integrate)

**Step 3: Update CLI implementation**

```python
# flightfinder/cli.py
"""CLI entry point for FlightFinder."""

import asyncio
import webbrowser

import click
from rich.console import Console
from rich.prompt import Prompt

from flightfinder.api.serpapi import SerpAPIClient
from flightfinder.compare import PriceComparator
from flightfinder.config import get_config
from flightfinder.interactive import InteractiveSearch
from flightfinder.models import SearchParams
from flightfinder.output import OutputFormatter
from flightfinder.search import SearchOrchestrator

console = Console()


@click.group()
@click.version_option()
def main():
    """Find the cheapest flights from multiple origins."""
    pass


async def run_search(params: SearchParams) -> list:
    """Execute flight search with given parameters."""
    config = get_config()

    if not config.serpapi_key:
        console.print("[red]Error: FLIGHTFINDER_SERPAPI_KEY environment variable not set.[/red]")
        console.print("Get an API key at https://serpapi.com/")
        return []

    client = SerpAPIClient(api_key=config.serpapi_key)
    orchestrator = SearchOrchestrator(api_client=client)
    comparator = PriceComparator()

    console.print(f"\n[dim]Searching {len(params.origins)} origins...[/dim]")

    results = await orchestrator.search(params)

    # Apply filters
    if params.max_price:
        results = comparator.filter_by_price(results, params.max_price)
    if params.max_stops is not None:
        results = comparator.filter_by_stops(results, params.max_stops)

    # Sort and limit
    results = comparator.top_n(results, 10)

    return results


def display_results(results: list):
    """Display results and handle selection."""
    formatter = OutputFormatter()
    formatter.print_results(results)

    if not results:
        return

    while True:
        choice = Prompt.ask("\nDetails for # (or 'q' to quit)", default="q")
        if choice.lower() == "q":
            break

        try:
            index = int(choice)
            if 1 <= index <= len(results):
                option = results[index - 1]
                formatter.print_detail(option, index)

                # Open in browser
                console.print("\n[dim]Opening in browser...[/dim]")
                webbrowser.open(option.booking_url)
            else:
                console.print("[red]Invalid selection.[/red]")
        except ValueError:
            console.print("[red]Please enter a number or 'q'.[/red]")


@main.command()
@click.argument("origin")
@click.argument("destination")
@click.argument("depart_date")
@click.argument("return_date", required=False)
def quick(origin: str, destination: str, depart_date: str, return_date: str | None):
    """Quick search with defaults: flightfinder quick JFK YAO 2025-03-15 2025-03-25"""
    params = SearchParams(
        origins=[o.strip().upper() for o in origin.split(",")],
        destination=destination.upper(),
        depart_date=depart_date,
        return_date=return_date,
    )

    results = asyncio.run(run_search(params))
    display_results(results)


@main.command()
def search():
    """Interactive search with all options."""
    interactive = InteractiveSearch()
    params = interactive.run()

    results = asyncio.run(run_search(params))
    display_results(results)


@main.command()
def update_routes():
    """Refresh the airline routes database."""
    console.print("[yellow]Route database update not yet implemented.[/yellow]")
    console.print("This will download routes from OpenFlights database.")


if __name__ == "__main__":
    main()
```

**Step 4: Run tests to verify they pass**

Run: `pytest tests/test_cli.py -v`
Expected: PASS

**Step 5: Commit**

```bash
git add flightfinder/cli.py tests/test_cli.py
git commit -m "feat(cli): wire up CLI commands with search and output"
```

---

## Task 11: JSON Output for n8n

**Files:**
- Modify: `flightfinder/cli.py`
- Modify: `flightfinder/output.py`
- Test: `tests/test_output.py` (update)

**Step 1: Write the failing test**

```python
# Add to tests/test_output.py

import json

class TestJSONOutput:
    """Tests for JSON output formatting."""

    def test_to_json_dict(self, formatter, sample_option):
        """Test converting option to JSON-serializable dict."""
        result = formatter.to_dict(sample_option)

        assert result["price"] == 1203.0
        assert result["currency"] == "USD"
        assert result["booking_type"] == "round-trip"
        assert result["booking_url"] == "https://google.com/flights/123"
        assert "outbound" in result

    def test_to_json_string(self, formatter, sample_option):
        """Test converting options to JSON string."""
        json_str = formatter.to_json([sample_option])

        data = json.loads(json_str)
        assert len(data) == 1
        assert data[0]["price"] == 1203.0
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/test_output.py::TestJSONOutput -v`
Expected: FAIL

**Step 3: Update output.py**

```python
# Add to flightfinder/output.py

import json

# Add these methods to OutputFormatter class:

    def to_dict(self, option: FlightOption) -> dict:
        """Convert FlightOption to JSON-serializable dict."""
        return {
            "price": option.total_price,
            "currency": option.currency,
            "booking_type": option.booking_type.value,
            "booking_url": option.booking_url,
            "is_skiplagged": option.is_skiplagged,
            "outbound": [
                {
                    "origin": leg.origin,
                    "destination": leg.destination,
                    "airline": leg.airline,
                    "flight_number": leg.flight_number,
                    "departure": leg.departure.isoformat(),
                    "arrival": leg.arrival.isoformat(),
                    "duration_minutes": leg.duration_minutes,
                }
                for leg in option.outbound_legs
            ],
            "return": [
                {
                    "origin": leg.origin,
                    "destination": leg.destination,
                    "airline": leg.airline,
                    "flight_number": leg.flight_number,
                    "departure": leg.departure.isoformat(),
                    "arrival": leg.arrival.isoformat(),
                    "duration_minutes": leg.duration_minutes,
                }
                for leg in (option.return_legs or [])
            ],
            "stops_outbound": option.total_stops_outbound,
            "stops_return": option.total_stops_return,
        }

    def to_json(self, options: list[FlightOption]) -> str:
        """Convert list of options to JSON string."""
        return json.dumps([self.to_dict(opt) for opt in options], indent=2)
```

**Step 4: Add --json flag to CLI**

```python
# Update quick command in cli.py to accept --json flag:

@main.command()
@click.argument("origin")
@click.argument("destination")
@click.argument("depart_date")
@click.argument("return_date", required=False)
@click.option("--json", "output_json", is_flag=True, help="Output as JSON")
def quick(origin: str, destination: str, depart_date: str, return_date: str | None, output_json: bool):
    """Quick search with defaults: flightfinder quick JFK YAO 2025-03-15 2025-03-25"""
    params = SearchParams(
        origins=[o.strip().upper() for o in origin.split(",")],
        destination=destination.upper(),
        depart_date=depart_date,
        return_date=return_date,
    )

    results = asyncio.run(run_search(params))

    if output_json:
        formatter = OutputFormatter()
        click.echo(formatter.to_json(results))
    else:
        display_results(results)
```

**Step 5: Run tests to verify they pass**

Run: `pytest tests/test_output.py -v`
Expected: PASS

**Step 6: Commit**

```bash
git add flightfinder/cli.py flightfinder/output.py tests/test_output.py
git commit -m "feat(output): add JSON output for n8n integration"
```

---

## Task 12: Monitor Commands for n8n Export

**Files:**
- Create: `flightfinder/export.py`
- Test: `tests/test_export.py`
- Modify: `flightfinder/cli.py`

**Step 1: Write the failing test**

```python
# tests/test_export.py
"""Tests for n8n workflow export."""

import json

import pytest

from flightfinder.export import N8NExporter


class TestN8NExporter:
    """Tests for n8n workflow export."""

    @pytest.fixture
    def exporter(self):
        """Create exporter."""
        return N8NExporter()

    def test_generate_workflow_json(self, exporter):
        """Test generating n8n workflow JSON."""
        workflow = exporter.generate_workflow(
            name="cameroon-march",
            command="flightfinder quick JFK YAO 2025-03-15 2025-03-25 --json",
            alert_threshold=1200.0,
            schedule="0 9 * * *",  # Daily at 9am
        )

        # Should be valid JSON
        data = json.loads(workflow)

        assert data["name"] == "cameroon-march"
        assert "nodes" in data
        assert "connections" in data

    def test_workflow_has_schedule_trigger(self, exporter):
        """Test workflow includes schedule trigger node."""
        workflow = exporter.generate_workflow(
            name="test",
            command="flightfinder quick JFK YAO 2025-03-15",
            schedule="0 9 * * *",
        )

        data = json.loads(workflow)
        node_types = [n["type"] for n in data["nodes"]]

        assert "n8n-nodes-base.scheduleTrigger" in node_types

    def test_workflow_has_execute_command(self, exporter):
        """Test workflow includes execute command node."""
        workflow = exporter.generate_workflow(
            name="test",
            command="flightfinder quick JFK YAO 2025-03-15 --json",
        )

        data = json.loads(workflow)
        node_types = [n["type"] for n in data["nodes"]]

        assert "n8n-nodes-base.executeCommand" in node_types
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/test_export.py -v`
Expected: FAIL with "ModuleNotFoundError"

**Step 3: Write minimal implementation**

```python
# flightfinder/export.py
"""N8N workflow export for flight monitoring."""

import json


class N8NExporter:
    """Generate n8n workflow JSON for flight monitoring."""

    def generate_workflow(
        self,
        name: str,
        command: str,
        alert_threshold: float | None = None,
        schedule: str = "0 9 * * *",
    ) -> str:
        """Generate n8n workflow JSON.

        Args:
            name: Workflow name
            command: CLI command to execute
            alert_threshold: Price threshold for alerts (optional)
            schedule: Cron schedule (default: daily at 9am)
        """
        workflow = {
            "name": name,
            "nodes": [
                {
                    "parameters": {
                        "rule": {"interval": [{"field": "cronExpression", "expression": schedule}]}
                    },
                    "id": "schedule",
                    "name": "Schedule Trigger",
                    "type": "n8n-nodes-base.scheduleTrigger",
                    "typeVersion": 1.1,
                    "position": [0, 0],
                },
                {
                    "parameters": {"command": command},
                    "id": "execute",
                    "name": "Run FlightFinder",
                    "type": "n8n-nodes-base.executeCommand",
                    "typeVersion": 1,
                    "position": [220, 0],
                },
                {
                    "parameters": {
                        "jsCode": f"""
const results = JSON.parse($input.first().json.stdout);
const threshold = {alert_threshold or 'null'};

if (threshold && results.length > 0) {{
  const cheapest = results[0];
  if (cheapest.price < threshold) {{
    return [{{ json: {{ alert: true, ...cheapest }} }}];
  }}
}}
return [{{ json: {{ alert: false, results }} }}];
"""
                    },
                    "id": "check",
                    "name": "Check Threshold",
                    "type": "n8n-nodes-base.code",
                    "typeVersion": 2,
                    "position": [440, 0],
                },
            ],
            "connections": {
                "Schedule Trigger": {"main": [[{"node": "Run FlightFinder", "type": "main", "index": 0}]]},
                "Run FlightFinder": {"main": [[{"node": "Check Threshold", "type": "main", "index": 0}]]},
            },
        }

        return json.dumps(workflow, indent=2)
```

**Step 4: Run tests to verify they pass**

Run: `pytest tests/test_export.py -v`
Expected: PASS

**Step 5: Add monitor commands to CLI**

```python
# Add to flightfinder/cli.py

from flightfinder.export import N8NExporter

@main.group()
def monitor():
    """Manage saved flight monitors."""
    pass


@monitor.command("export")
@click.option("--name", required=True, help="Monitor name")
@click.option("--from", "origins", required=True, help="Origin airports (comma-separated)")
@click.option("--to", "destination", required=True, help="Destination airport")
@click.option("--depart", required=True, help="Departure date")
@click.option("--return", "return_date", help="Return date")
@click.option("--alert-below", type=float, help="Alert when price below this")
@click.option("--schedule", default="0 9 * * *", help="Cron schedule")
def monitor_export(name, origins, destination, depart, return_date, alert_below, schedule):
    """Export a monitor as n8n workflow JSON."""
    # Build the command
    cmd_parts = ["flightfinder", "quick", origins, destination, depart]
    if return_date:
        cmd_parts.append(return_date)
    cmd_parts.append("--json")
    command = " ".join(cmd_parts)

    exporter = N8NExporter()
    workflow = exporter.generate_workflow(
        name=name,
        command=command,
        alert_threshold=alert_below,
        schedule=schedule,
    )

    console.print(workflow)
    console.print(f"\n[green]Workflow exported. Import into n8n to start monitoring.[/green]")
```

**Step 6: Commit**

```bash
git add flightfinder/cli.py flightfinder/export.py tests/test_export.py
git commit -m "feat(monitor): add n8n workflow export for monitoring"
```

---

## Summary

This plan implements FlightFinder in 12 bite-sized tasks:

1. **Config** - Environment variable loading
2. **Database** - SQLite connection and tables
3. **Routes** - Route cache operations
4. **SerpAPI** - Google Flights API client
5. **Search** - Multi-origin search orchestration
6. **Compare** - Price comparison and ranking
7. **Skiplagged** - Hidden city route discovery
8. **Interactive** - Interactive mode prompts
9. **Output** - Rich terminal formatting
10. **CLI Wiring** - Connect all components
11. **JSON Output** - n8n-compatible output
12. **Monitor Export** - n8n workflow generation

Each task follows TDD: write failing test → implement → verify → commit.
