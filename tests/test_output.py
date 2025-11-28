"""Tests for Rich output formatting."""

import json
from datetime import datetime

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

    def test_format_price_usd(self, formatter):
        """Test USD price formatting."""
        assert formatter.format_price(1203.0, "USD") == "$1,203"

    def test_format_price_rounds_up(self, formatter):
        """Test price rounds to nearest dollar."""
        assert formatter.format_price(999.99, "USD") == "$1,000"

    def test_format_price_other_currency(self, formatter):
        """Test non-USD currency formatting."""
        assert formatter.format_price(1500.0, "EUR") == "1,500 EUR"

    def test_format_duration_hours_minutes(self, formatter):
        """Test duration formatting with hours and minutes."""
        assert formatter.format_duration(90) == "1h 30m"

    def test_format_duration_exact_hours(self, formatter):
        """Test duration formatting for exact hours."""
        assert formatter.format_duration(60) == "1h 0m"

    def test_format_duration_minutes_only(self, formatter):
        """Test duration formatting for less than an hour."""
        assert formatter.format_duration(45) == "0h 45m"

    def test_format_time(self, formatter):
        """Test time formatting."""
        dt = datetime(2025, 3, 15, 18, 30)
        assert formatter.format_time(dt) == "18:30"

    def test_format_date(self, formatter):
        """Test date formatting."""
        dt = datetime(2025, 3, 15, 18, 30)
        assert formatter.format_date(dt) == "Mar 15"

    def test_format_stops_direct(self, formatter):
        """Test direct flight formatting."""
        assert formatter.format_stops(0) == "Direct"

    def test_format_stops_singular(self, formatter):
        """Test 1 stop formatting."""
        assert formatter.format_stops(1) == "1 stop"

    def test_format_stops_plural(self, formatter):
        """Test multiple stops formatting."""
        assert formatter.format_stops(2) == "2 stops"

    def test_format_booking_type_round_trip(self, formatter):
        """Test round-trip booking type formatting."""
        assert formatter.format_booking_type(BookingType.ROUND_TRIP) == "round-trip"

    def test_format_booking_type_skiplagged(self, formatter):
        """Test skiplagged booking type formatting."""
        assert formatter.format_booking_type(BookingType.SKIPLAGGED) == "skiplagged"

    def test_format_booking_type_two_oneways(self, formatter):
        """Test two-oneways booking type formatting."""
        assert formatter.format_booking_type(BookingType.TWO_ONE_WAYS) == "two-oneways"

    def test_build_results_table(self, formatter, sample_option):
        """Test building results table."""
        table = formatter.build_results_table([sample_option])
        # Table should have content
        assert table is not None
        assert table.row_count == 1

    def test_build_results_table_empty(self, formatter):
        """Test building results table with no options."""
        table = formatter.build_results_table([])
        assert table.row_count == 0

    def test_build_results_table_multiple(self, formatter, sample_option):
        """Test building results table with multiple options."""
        options = [sample_option, sample_option, sample_option]
        table = formatter.build_results_table(options)
        assert table.row_count == 3


class TestJSONOutput:
    """Tests for JSON output formatting."""

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

    def test_to_dict(self, formatter, sample_option):
        """Test converting option to JSON-serializable dict."""
        result = formatter.to_dict(sample_option)

        assert result["price"] == 1203.0
        assert result["currency"] == "USD"
        assert result["booking_type"] == "round-trip"
        assert result["booking_url"] == "https://google.com/flights/123"
        assert "outbound" in result

    def test_to_dict_outbound_details(self, formatter, sample_option):
        """Test outbound leg details in dict."""
        result = formatter.to_dict(sample_option)

        assert len(result["outbound"]) == 1
        leg = result["outbound"][0]
        assert leg["origin"] == "JFK"
        assert leg["destination"] == "YAO"
        assert leg["airline"] == "Air France"
        assert leg["flight_number"] == "AF007"

    def test_to_json_string(self, formatter, sample_option):
        """Test converting options to JSON string."""
        json_str = formatter.to_json([sample_option])

        data = json.loads(json_str)
        assert len(data) == 1
        assert data[0]["price"] == 1203.0

    def test_to_json_empty_list(self, formatter):
        """Test converting empty list to JSON."""
        json_str = formatter.to_json([])

        data = json.loads(json_str)
        assert data == []

    def test_to_dict_with_return_flight(self, formatter):
        """Test dict includes return flight details."""
        outbound = FlightLeg(
            "JFK", "YAO", "AF", "AF007",
            datetime(2025, 3, 15, 18, 30),
            datetime(2025, 3, 16, 17, 45),
            840,
        )
        return_leg = FlightLeg(
            "YAO", "JFK", "ET", "ET100",
            datetime(2025, 3, 25, 10, 0),
            datetime(2025, 3, 25, 20, 0),
            600,
        )
        option = FlightOption(
            outbound_legs=[outbound],
            return_legs=[return_leg],
            total_price=1500.0,
            currency="USD",
            booking_type=BookingType.ROUND_TRIP,
            booking_url="https://example.com",
        )

        result = formatter.to_dict(option)

        assert len(result["return"]) == 1
        assert result["return"][0]["origin"] == "YAO"
        assert result["return"][0]["destination"] == "JFK"
