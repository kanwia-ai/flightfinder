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
            FlightOption(
                [leg1, leg2], None, 1000, "USD", BookingType.ONE_WAY, "url1"
            ),  # 1 stop
            FlightOption(
                [leg1], None, 1100, "USD", BookingType.ONE_WAY, "url2"
            ),  # 0 stops
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
            outbound_legs=[
                FlightLeg("JFK", "YAO", "AF", "AF1", datetime.now(), datetime.now(), 400)
            ],
            return_legs=None,
            total_price=600.0,
            currency="USD",
            booking_type=BookingType.ONE_WAY,
            booking_url="url1",
        )
        return_flight = FlightOption(
            outbound_legs=[
                FlightLeg("YAO", "JFK", "ET", "ET1", datetime.now(), datetime.now(), 450)
            ],
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
