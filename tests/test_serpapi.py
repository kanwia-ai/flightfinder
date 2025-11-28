"""Tests for SerpAPI client."""

import json
from pathlib import Path
from unittest.mock import AsyncMock, patch

import pytest

from flightfinder.api.serpapi import SerpAPIClient
from flightfinder.models import FlightOption


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
