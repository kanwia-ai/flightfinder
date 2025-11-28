"""Tests for data models."""

from datetime import datetime

from flightfinder.models import (
    BookingType,
    CabinClass,
    FlightLeg,
    FlightOption,
    SearchParams,
)


class TestFlightLeg:
    """Tests for FlightLeg dataclass."""

    def test_create_flight_leg(self):
        """Test creating a flight leg with all required fields."""
        leg = FlightLeg(
            origin="JFK",
            destination="CDG",
            airline="AF",
            flight_number="AF007",
            departure=datetime(2025, 3, 15, 18, 30),
            arrival=datetime(2025, 3, 16, 8, 15),
            duration_minutes=465,
        )
        assert leg.origin == "JFK"
        assert leg.destination == "CDG"
        assert leg.airline == "AF"
        assert leg.flight_number == "AF007"
        assert leg.duration_minutes == 465


class TestFlightOption:
    """Tests for FlightOption dataclass."""

    def test_total_stops_outbound(self):
        """Test calculating outbound stops."""
        leg1 = FlightLeg(
            origin="JFK",
            destination="CDG",
            airline="AF",
            flight_number="AF007",
            departure=datetime(2025, 3, 15, 18, 30),
            arrival=datetime(2025, 3, 16, 8, 15),
            duration_minutes=465,
        )
        leg2 = FlightLeg(
            origin="CDG",
            destination="YAO",
            airline="AF",
            flight_number="AF840",
            departure=datetime(2025, 3, 16, 10, 30),
            arrival=datetime(2025, 3, 16, 17, 45),
            duration_minutes=375,
        )
        option = FlightOption(
            outbound_legs=[leg1, leg2],
            return_legs=None,
            total_price=1043.0,
            currency="USD",
            booking_type=BookingType.ONE_WAY,
            booking_url="https://google.com/flights",
        )
        assert option.total_stops_outbound == 1
        assert option.total_stops_return is None

    def test_round_trip_stops(self):
        """Test calculating stops for round trip."""
        outbound = FlightLeg(
            origin="JFK",
            destination="YAO",
            airline="AF",
            flight_number="AF007",
            departure=datetime(2025, 3, 15, 18, 30),
            arrival=datetime(2025, 3, 16, 17, 45),
            duration_minutes=840,
        )
        return_leg = FlightLeg(
            origin="YAO",
            destination="JFK",
            airline="AF",
            flight_number="AF008",
            departure=datetime(2025, 3, 25, 9, 15),
            arrival=datetime(2025, 3, 25, 21, 30),
            duration_minutes=855,
        )
        option = FlightOption(
            outbound_legs=[outbound],
            return_legs=[return_leg],
            total_price=1203.0,
            currency="USD",
            booking_type=BookingType.ROUND_TRIP,
            booking_url="https://google.com/flights",
        )
        assert option.total_stops_outbound == 0
        assert option.total_stops_return == 0


class TestSearchParams:
    """Tests for SearchParams dataclass."""

    def test_minimal_search_params(self):
        """Test creating search params with minimal required fields."""
        params = SearchParams(
            origins=["JFK"],
            destination="YAO",
            depart_date="2025-03-15",
        )
        assert params.origins == ["JFK"]
        assert params.destination == "YAO"
        assert params.depart_date == "2025-03-15"
        assert params.return_date is None
        assert params.flex_days == 0
        assert params.cabin == CabinClass.ECONOMY
        assert params.include_skiplagged is False

    def test_full_search_params(self):
        """Test creating search params with all options."""
        params = SearchParams(
            origins=["JFK", "EWR", "IAD"],
            destination="YAO",
            depart_date="2025-03-15",
            return_date="2025-03-25",
            flex_days=3,
            depart_after="18:00",
            arrive_before="12:00",
            max_stops=1,
            max_duration_minutes=1440,
            cabin=CabinClass.BUSINESS,
            airlines_exclude=["Spirit", "Frontier"],
            min_layover_minutes=60,
            max_layover_minutes=240,
            max_price=1500.0,
            alert_below=1200.0,
            include_skiplagged=True,
            nearby_km=100,
        )
        assert len(params.origins) == 3
        assert params.flex_days == 3
        assert params.max_stops == 1
        assert params.cabin == CabinClass.BUSINESS
        assert params.include_skiplagged is True
        assert params.nearby_km == 100


class TestBookingType:
    """Tests for BookingType enum."""

    def test_booking_type_values(self):
        """Test all booking type values exist."""
        assert BookingType.ROUND_TRIP.value == "round-trip"
        assert BookingType.ONE_WAY.value == "one-way"
        assert BookingType.TWO_ONE_WAYS.value == "two-oneways"
        assert BookingType.OPEN_JAW.value == "open-jaw"
        assert BookingType.SKIPLAGGED.value == "skiplagged"
