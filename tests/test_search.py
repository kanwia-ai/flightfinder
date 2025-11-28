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
