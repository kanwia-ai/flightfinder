"""Rich terminal output formatting."""

import json
from datetime import datetime

from rich.console import Console
from rich.table import Table

from flightfinder.models import BookingType, FlightOption


class OutputFormatter:
    """Format flight results for terminal output."""

    def __init__(self):
        """Initialize with Rich console."""
        self.console = Console()

    def format_price(self, price: float, currency: str) -> str:
        """Format price with currency symbol."""
        if currency == "USD":
            return f"${price:,.0f}"
        return f"{price:,.0f} {currency}"

    def format_duration(self, minutes: int) -> str:
        """Format duration in hours and minutes."""
        hours = minutes // 60
        mins = minutes % 60
        return f"{hours}h {mins}m"

    def format_time(self, dt: datetime) -> str:
        """Format time as HH:MM."""
        return dt.strftime("%H:%M")

    def format_date(self, dt: datetime) -> str:
        """Format date as Mon DD."""
        return dt.strftime("%b %d")

    def format_stops(self, stops: int) -> str:
        """Format number of stops."""
        if stops == 0:
            return "Direct"
        if stops == 1:
            return "1 stop"
        return f"{stops} stops"

    def format_booking_type(self, booking_type: BookingType) -> str:
        """Format booking type for display."""
        return booking_type.value

    def build_results_table(self, options: list[FlightOption]) -> Table:
        """Build Rich table with search results."""
        table = Table(title="Flight Results")

        table.add_column("#", justify="right", style="cyan")
        table.add_column("Price", justify="right", style="green")
        table.add_column("Type", style="yellow")
        table.add_column("Route")
        table.add_column("Outbound")
        table.add_column("Stops", justify="center")

        for i, option in enumerate(options, 1):
            # Build route string
            if option.outbound_legs:
                origin = option.outbound_legs[0].origin
                dest = option.outbound_legs[-1].destination
                route = f"{origin} -> {dest}"
            else:
                route = "N/A"

            # Outbound timing
            if option.outbound_legs:
                dep = option.outbound_legs[0].departure
                outbound = f"{self.format_date(dep)} {self.format_time(dep)}"
            else:
                outbound = "N/A"

            table.add_row(
                str(i),
                self.format_price(option.total_price, option.currency),
                self.format_booking_type(option.booking_type),
                route,
                outbound,
                self.format_stops(option.total_stops_outbound),
            )

        return table

    def print_results(self, options: list[FlightOption]):
        """Print results table to console."""
        if not options:
            self.console.print(
                "[yellow]No flights found matching your criteria.[/yellow]"
            )
            return

        table = self.build_results_table(options)
        self.console.print(table)

    def print_detail(self, option: FlightOption, index: int):
        """Print detailed flight information."""
        price_str = self.format_price(option.total_price, option.currency)
        type_str = self.format_booking_type(option.booking_type)
        self.console.print(f"\n[bold]FLIGHT #{index}[/bold] - {price_str} ({type_str})")

        if option.is_skiplagged:
            self.console.print(
                f"\n[bold red]WARNING: SKIPLAGGED:[/bold red] "
                f"Book to {option.skiplagged_deplane_at}, deplane early. No checked bags."
            )

        self.console.print("\n[bold]OUTBOUND[/bold]")
        for leg in option.outbound_legs:
            self.console.print(
                f"  {leg.origin} {self.format_time(leg.departure)} -> "
                f"{leg.destination} {self.format_time(leg.arrival)} "
                f"({leg.airline} {leg.flight_number}) - "
                f"{self.format_duration(leg.duration_minutes)}"
            )

        if option.return_legs:
            self.console.print("\n[bold]RETURN[/bold]")
            for leg in option.return_legs:
                self.console.print(
                    f"  {leg.origin} {self.format_time(leg.departure)} -> "
                    f"{leg.destination} {self.format_time(leg.arrival)} "
                    f"({leg.airline} {leg.flight_number}) - "
                    f"{self.format_duration(leg.duration_minutes)}"
                )

        self.console.print(f"\n[dim]Booking: {option.booking_url}[/dim]")

    def to_dict(self, option: FlightOption) -> dict:
        """Convert FlightOption to JSON-serializable dict."""
        return {
            "price": option.total_price,
            "currency": option.currency,
            "booking_type": option.booking_type.value,
            "booking_url": option.booking_url,
            "is_skiplagged": option.is_skiplagged,
            "outbound": [
                {
                    "origin": leg.origin,
                    "destination": leg.destination,
                    "airline": leg.airline,
                    "flight_number": leg.flight_number,
                    "departure": leg.departure.isoformat(),
                    "arrival": leg.arrival.isoformat(),
                    "duration_minutes": leg.duration_minutes,
                }
                for leg in option.outbound_legs
            ],
            "return": [
                {
                    "origin": leg.origin,
                    "destination": leg.destination,
                    "airline": leg.airline,
                    "flight_number": leg.flight_number,
                    "departure": leg.departure.isoformat(),
                    "arrival": leg.arrival.isoformat(),
                    "duration_minutes": leg.duration_minutes,
                }
                for leg in (option.return_legs or [])
            ],
            "stops_outbound": option.total_stops_outbound,
            "stops_return": option.total_stops_return,
        }

    def to_json(self, options: list[FlightOption]) -> str:
        """Convert list of options to JSON string."""
        return json.dumps([self.to_dict(opt) for opt in options], indent=2)
