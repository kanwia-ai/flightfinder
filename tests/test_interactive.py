"""Tests for interactive mode prompts."""

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

    def test_parse_airports_lowercase(self, interactive):
        """Test parsing converts to uppercase."""
        result = interactive._parse_airports("jfk, ewr")
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

    def test_parse_time_whitespace(self, interactive):
        """Test parsing time with whitespace."""
        result = interactive._parse_time("  18:30  ")
        assert result == "18:30"

    def test_parse_duration_hours(self, interactive):
        """Test parsing duration in hours."""
        result = interactive._parse_duration("24h")
        assert result == 1440  # minutes

    def test_parse_duration_minutes(self, interactive):
        """Test parsing duration in minutes."""
        result = interactive._parse_duration("90m")
        assert result == 90

    def test_parse_duration_empty(self, interactive):
        """Test parsing empty duration returns None."""
        result = interactive._parse_duration("")
        assert result is None

    def test_parse_duration_any(self, interactive):
        """Test parsing 'any' duration returns None."""
        result = interactive._parse_duration("any")
        assert result is None

    def test_parse_duration_invalid(self, interactive):
        """Test parsing invalid duration returns None."""
        result = interactive._parse_duration("invalid")
        assert result is None

    def test_parse_cabin_economy(self, interactive):
        """Test parsing economy cabin class."""
        assert interactive._parse_cabin("economy") == CabinClass.ECONOMY

    def test_parse_cabin_business(self, interactive):
        """Test parsing business cabin class."""
        assert interactive._parse_cabin("business") == CabinClass.BUSINESS

    def test_parse_cabin_premium(self, interactive):
        """Test parsing premium economy cabin class."""
        assert interactive._parse_cabin("premium") == CabinClass.PREMIUM_ECONOMY

    def test_parse_cabin_first(self, interactive):
        """Test parsing first class cabin."""
        assert interactive._parse_cabin("first") == CabinClass.FIRST

    def test_parse_cabin_default(self, interactive):
        """Test parsing empty cabin defaults to economy."""
        assert interactive._parse_cabin("") == CabinClass.ECONOMY

    def test_parse_bool_yes(self, interactive):
        """Test parsing yes values."""
        assert interactive._parse_bool("y") is True
        assert interactive._parse_bool("yes") is True
        assert interactive._parse_bool("true") is True
        assert interactive._parse_bool("1") is True

    def test_parse_bool_no(self, interactive):
        """Test parsing no values."""
        assert interactive._parse_bool("n") is False
        assert interactive._parse_bool("no") is False
        assert interactive._parse_bool("") is False

    def test_parse_int_valid(self, interactive):
        """Test parsing valid integer."""
        assert interactive._parse_int("5") == 5

    def test_parse_int_empty(self, interactive):
        """Test parsing empty returns None."""
        assert interactive._parse_int("") is None

    def test_parse_int_any(self, interactive):
        """Test parsing 'any' returns None."""
        assert interactive._parse_int("any") is None

    def test_parse_int_invalid(self, interactive):
        """Test parsing invalid returns None."""
        assert interactive._parse_int("abc") is None

    def test_parse_float_valid(self, interactive):
        """Test parsing valid float."""
        assert interactive._parse_float("1500.50") == 1500.50

    def test_parse_float_empty(self, interactive):
        """Test parsing empty returns None."""
        assert interactive._parse_float("") is None

    def test_build_params_basic(self, interactive):
        """Test building SearchParams from basic responses."""
        responses = {
            "origins": "JFK, EWR",
            "destination": "YAO",
            "depart_date": "2025-03-15",
            "return_date": "2025-03-25",
        }

        params = interactive._build_params(responses)

        assert isinstance(params, SearchParams)
        assert params.origins == ["JFK", "EWR"]
        assert params.destination == "YAO"
        assert params.depart_date == "2025-03-15"
        assert params.return_date == "2025-03-25"

    def test_build_params_with_options(self, interactive):
        """Test building SearchParams with all options."""
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

        assert params.origins == ["JFK", "EWR"]
        assert params.destination == "YAO"
        assert params.depart_after == "18:00"
        assert params.max_stops == 1
        assert params.include_skiplagged is True

    def test_build_params_oneway(self, interactive):
        """Test building params for one-way trip."""
        responses = {
            "origins": "JFK",
            "destination": "YAO",
            "depart_date": "2025-03-15",
            "return_date": "oneway",
        }

        params = interactive._build_params(responses)

        assert params.return_date is None

    def test_build_params_with_price_limits(self, interactive):
        """Test building params with price constraints."""
        responses = {
            "origins": "JFK",
            "destination": "YAO",
            "depart_date": "2025-03-15",
            "return_date": "",
            "max_price": "2000",
            "alert_below": "1500",
        }

        params = interactive._build_params(responses)

        assert params.max_price == 2000.0
        assert params.alert_below == 1500.0

    def test_build_params_with_layover_times(self, interactive):
        """Test building params with layover constraints."""
        responses = {
            "origins": "JFK",
            "destination": "YAO",
            "depart_date": "2025-03-15",
            "return_date": "",
            "layover_min": "60m",
            "layover_max": "3h",
        }

        params = interactive._build_params(responses)

        assert params.min_layover_minutes == 60
        assert params.max_layover_minutes == 180
