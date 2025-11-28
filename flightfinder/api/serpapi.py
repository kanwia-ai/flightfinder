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
