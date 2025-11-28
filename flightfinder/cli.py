"""CLI entry point for FlightFinder."""

import asyncio
import webbrowser

import click
from rich.console import Console
from rich.prompt import Prompt

from flightfinder.api.serpapi import SerpAPIClient, SerpAPIError
from flightfinder.compare import PriceComparator
from flightfinder.config import get_config
from flightfinder.export import N8NExporter
from flightfinder.interactive import InteractiveSearch
from flightfinder.models import SearchParams
from flightfinder.output import OutputFormatter
from flightfinder.search import SearchOrchestrator

console = Console()


@click.group()
@click.version_option()
def main():
    """Find the cheapest flights from multiple origins."""
    pass


async def run_search(params: SearchParams) -> list:
    """Execute flight search with given parameters."""
    config = get_config()

    if not config.serpapi_key:
        console.print(
            "[red]Error: FLIGHTFINDER_SERPAPI_KEY environment variable not set.[/red]"
        )
        console.print("Get an API key at https://serpapi.com/")
        return []

    client = SerpAPIClient(api_key=config.serpapi_key)
    orchestrator = SearchOrchestrator(api_client=client)
    comparator = PriceComparator()

    console.print(f"\n[dim]Searching {len(params.origins)} origins...[/dim]")

    try:
        results = await orchestrator.search(params)
    except SerpAPIError as e:
        console.print(f"[red]Search error: {e}[/red]")
        return []

    # Apply filters
    if params.max_price:
        results = comparator.filter_by_price(results, params.max_price)
    if params.max_stops is not None:
        results = comparator.filter_by_stops(results, params.max_stops)

    # Sort and limit
    results = comparator.top_n(results, 10)

    return results


def display_results(results: list):
    """Display results and handle selection."""
    formatter = OutputFormatter()
    formatter.print_results(results)

    if not results:
        return

    while True:
        choice = Prompt.ask("\nDetails for # (or 'q' to quit)", default="q")
        if choice.lower() == "q":
            break

        try:
            index = int(choice)
            if 1 <= index <= len(results):
                option = results[index - 1]
                formatter.print_detail(option, index)

                # Open in browser
                open_choice = Prompt.ask("Open in browser?", default="y")
                if open_choice.lower() in ("y", "yes"):
                    console.print("\n[dim]Opening in browser...[/dim]")
                    webbrowser.open(option.booking_url)
            else:
                console.print("[red]Invalid selection.[/red]")
        except ValueError:
            console.print("[red]Please enter a number or 'q'.[/red]")


@main.command()
@click.argument("origin")
@click.argument("destination")
@click.argument("depart_date")
@click.argument("return_date", required=False)
@click.option("--json", "output_json", is_flag=True, help="Output as JSON for n8n")
def quick(
    origin: str,
    destination: str,
    depart_date: str,
    return_date: str | None,
    output_json: bool,
):
    """Quick search with defaults: flightfinder quick JFK YAO 2025-03-15 2025-03-25"""
    params = SearchParams(
        origins=[o.strip().upper() for o in origin.split(",")],
        destination=destination.upper(),
        depart_date=depart_date,
        return_date=return_date,
    )

    results = asyncio.run(run_search(params))

    if output_json:
        formatter = OutputFormatter()
        click.echo(formatter.to_json(results))
    else:
        display_results(results)


@main.command()
def search():
    """Interactive search with all options."""
    interactive = InteractiveSearch()
    params = interactive.run()

    results = asyncio.run(run_search(params))
    display_results(results)


@main.command()
def update_routes():
    """Refresh the airline routes database."""
    console.print("[yellow]Route database update not yet implemented.[/yellow]")
    console.print("This will download routes from OpenFlights database.")


@main.group()
def monitor():
    """Manage saved flight monitors."""
    pass


@monitor.command("export")
@click.option("--name", required=True, help="Monitor name")
@click.option(
    "--from", "origins", required=True, help="Origin airports (comma-separated)"
)
@click.option("--to", "destination", required=True, help="Destination airport")
@click.option("--depart", required=True, help="Departure date")
@click.option("--return", "return_date", help="Return date")
@click.option("--alert-below", type=float, help="Alert when price below this")
@click.option("--schedule", default="0 9 * * *", help="Cron schedule")
def monitor_export(
    name: str,
    origins: str,
    destination: str,
    depart: str,
    return_date: str | None,
    alert_below: float | None,
    schedule: str,
):
    """Export a monitor as n8n workflow JSON."""
    # Build the command
    cmd_parts = ["flightfinder", "quick", origins, destination, depart]
    if return_date:
        cmd_parts.append(return_date)
    cmd_parts.append("--json")
    command = " ".join(cmd_parts)

    exporter = N8NExporter()
    workflow = exporter.generate_workflow(
        name=name,
        command=command,
        alert_threshold=alert_below,
        schedule=schedule,
    )

    click.echo(workflow)
    console.print(
        "\n[green]Workflow exported. Import into n8n to start monitoring.[/green]"
    )


if __name__ == "__main__":
    main()
