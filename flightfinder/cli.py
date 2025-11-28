"""CLI entry point for FlightFinder."""

import click


@click.group()
@click.version_option()
def main():
    """Find the cheapest flights from multiple origins."""
    pass


@main.command()
@click.argument("origin")
@click.argument("destination")
@click.argument("depart_date")
@click.argument("return_date", required=False)
def quick(origin: str, destination: str, depart_date: str, return_date: str | None):
    """Quick search with defaults: flightfinder quick JFK YAO 2025-03-15 2025-03-25"""
    click.echo(f"Searching {origin} → {destination}")
    click.echo(f"Depart: {depart_date}, Return: {return_date or 'one-way'}")
    # TODO: Implement search


@main.command()
def search():
    """Interactive search with all options."""
    click.echo("Interactive search mode - coming soon")
    # TODO: Implement interactive mode


@main.command()
def update_routes():
    """Refresh the airline routes database."""
    click.echo("Updating routes database - coming soon")
    # TODO: Implement route update


if __name__ == "__main__":
    main()
