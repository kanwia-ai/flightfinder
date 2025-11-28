"""Price comparison and ranking engine."""

from flightfinder.models import BookingType, FlightOption


class PriceComparator:
    """Compare and rank flight options by price."""

    def sort_by_price(self, options: list[FlightOption]) -> list[FlightOption]:
        """Sort options by total price, cheapest first."""
        return sorted(options, key=lambda opt: opt.total_price)

    def filter_by_price(
        self, options: list[FlightOption], max_price: float
    ) -> list[FlightOption]:
        """Filter options by maximum price."""
        return [opt for opt in options if opt.total_price <= max_price]

    def filter_by_stops(
        self, options: list[FlightOption], max_stops: int
    ) -> list[FlightOption]:
        """Filter options by maximum number of stops."""
        return [opt for opt in options if opt.total_stops_outbound <= max_stops]

    def top_n(self, options: list[FlightOption], n: int) -> list[FlightOption]:
        """Get the top N cheapest options."""
        sorted_options = self.sort_by_price(options)
        return sorted_options[:n]


def combine_one_ways(
    outbound: FlightOption, return_flight: FlightOption
) -> FlightOption:
    """Combine two one-way flights into a two-oneways option."""
    return FlightOption(
        outbound_legs=outbound.outbound_legs,
        return_legs=return_flight.outbound_legs,
        total_price=outbound.total_price + return_flight.total_price,
        currency=outbound.currency,
        booking_type=BookingType.TWO_ONE_WAYS,
        booking_url=f"{outbound.booking_url}|{return_flight.booking_url}",
    )
