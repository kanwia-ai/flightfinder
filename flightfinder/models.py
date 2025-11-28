"""Data models for FlightFinder."""

from dataclasses import dataclass
from datetime import datetime
from enum import Enum


class BookingType(Enum):
    """Type of flight booking structure."""

    ROUND_TRIP = "round-trip"
    ONE_WAY = "one-way"
    TWO_ONE_WAYS = "two-oneways"
    OPEN_JAW = "open-jaw"
    SKIPLAGGED = "skiplagged"


class CabinClass(Enum):
    """Cabin class for flights."""

    ECONOMY = "economy"
    PREMIUM_ECONOMY = "premium"
    BUSINESS = "business"
    FIRST = "first"


@dataclass
class FlightLeg:
    """A single flight leg (one takeoff and landing)."""

    origin: str
    destination: str
    airline: str
    flight_number: str
    departure: datetime
    arrival: datetime
    duration_minutes: int


@dataclass
class FlightOption:
    """A complete flight option with all legs and pricing."""

    outbound_legs: list[FlightLeg]
    return_legs: list[FlightLeg] | None
    total_price: float
    currency: str
    booking_type: BookingType
    booking_url: str
    is_skiplagged: bool = False
    skiplagged_deplane_at: str | None = None

    @property
    def total_stops_outbound(self) -> int:
        """Number of stops on outbound journey."""
        return len(self.outbound_legs) - 1

    @property
    def total_stops_return(self) -> int | None:
        """Number of stops on return journey."""
        if self.return_legs is None:
            return None
        return len(self.return_legs) - 1


@dataclass
class SearchParams:
    """Parameters for a flight search."""

    origins: list[str]
    destination: str
    depart_date: str
    return_date: str | None = None
    flex_days: int = 0
    depart_after: str | None = None
    depart_before: str | None = None
    arrive_after: str | None = None
    arrive_before: str | None = None
    return_depart_after: str | None = None
    return_depart_before: str | None = None
    return_arrive_after: str | None = None
    return_arrive_before: str | None = None
    max_stops: int | None = None
    max_duration_minutes: int | None = None
    cabin: CabinClass = CabinClass.ECONOMY
    airlines_include: list[str] | None = None
    airlines_exclude: list[str] | None = None
    min_layover_minutes: int = 45
    max_layover_minutes: int | None = None
    avoid_connections: list[str] | None = None
    max_price: float | None = None
    alert_below: float | None = None
    include_skiplagged: bool = False
    nearby_km: int | None = None
