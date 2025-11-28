"""Search orchestrator for flight searches."""

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
                    cabin=params.cabin,
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
