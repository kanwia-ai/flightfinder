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
        # Return original case-preserved value for time
        return value.strip()

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
        return_date_raw = responses.get("return_date", "")
        return_date = (
            None
            if return_date_raw.lower() in ("oneway", "")
            else return_date_raw
        )

        return SearchParams(
            origins=self._parse_airports(responses.get("origins", "")),
            destination=responses.get("destination", "").strip().upper(),
            depart_date=responses.get("depart_date", ""),
            return_date=return_date,
            depart_after=self._parse_time(responses.get("depart_after", "")),
            depart_before=self._parse_time(responses.get("depart_before", "")),
            arrive_after=self._parse_time(responses.get("arrive_after", "")),
            arrive_before=self._parse_time(responses.get("arrive_before", "")),
            max_stops=self._parse_int(responses.get("max_stops", "")),
            max_duration_minutes=self._parse_duration(
                responses.get("max_duration", "")
            ),
            cabin=self._parse_cabin(responses.get("cabin", "")),
            airlines_exclude=self._parse_airports(
                responses.get("airlines_avoid", "")
            ) or None,
            min_layover_minutes=self._parse_duration(
                responses.get("layover_min", "45m")
            ) or 45,
            max_layover_minutes=self._parse_duration(
                responses.get("layover_max", "")
            ),
            max_price=self._parse_float(responses.get("max_price", "")),
            alert_below=self._parse_float(responses.get("alert_below", "")),
            include_skiplagged=self._parse_bool(
                responses.get("include_skiplagged", "")
            ),
            nearby_km=self._parse_int(responses.get("nearby_km", "")),
        )

    def run(self) -> SearchParams:
        """Run interactive prompts and return SearchParams."""
        self.console.print("\n[bold]FlightFinder Interactive Search[/bold]\n")

        responses = {}

        responses["origins"] = Prompt.ask("Origin airports (comma-separated)")
        responses["destination"] = Prompt.ask("Destination")
        responses["nearby_km"] = Prompt.ask(
            "Search nearby airports within (km)", default="skip"
        )

        responses["depart_date"] = Prompt.ask("\nDeparture date (YYYY-MM-DD)")
        responses["flex_days"] = Prompt.ask("Flexible +/- days", default="0")
        responses["depart_after"] = Prompt.ask("Depart after", default="any")
        responses["arrive_before"] = Prompt.ask("Arrive before", default="any")

        responses["return_date"] = Prompt.ask(
            "\nReturn date (YYYY-MM-DD or 'oneway')"
        )

        responses["max_stops"] = Prompt.ask("\nMax stops", default="any")
        responses["max_duration"] = Prompt.ask("Max travel time", default="any")
        responses["cabin"] = Prompt.ask("Cabin", default="economy")
        responses["airlines_avoid"] = Prompt.ask(
            "Airlines to avoid", default="none"
        )
        responses["layover_min"] = Prompt.ask("Layover min", default="45m")
        responses["layover_max"] = Prompt.ask("Layover max", default="any")

        responses["max_price"] = Prompt.ask("\nMax price", default="any")
        responses["alert_below"] = Prompt.ask("Alert if below", default="none")

        responses["include_skiplagged"] = Prompt.ask(
            "\nInclude skiplagged fares?", default="n"
        )

        return self._build_params(responses)
