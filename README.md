# FlightFinder

CLI tool to find the cheapest flights from multiple origin airports with n8n integration for automated price monitoring.

## Features

- **Multi-origin search** - Compare prices from multiple airports at once (e.g., IAD,DCA,BWI)
- **Rich output table** - See airline, departure, arrival, stops, and layover airports at a glance
- **Cabin class support** - Defaults to economy, configurable for premium/business/first
- **JSON export** - Machine-readable output for automation pipelines
- **n8n integration** - Export monitors as n8n workflows for automated price alerts
- **Error handling** - Clear error messages for API issues and invalid searches

## Installation

```bash
git clone https://github.com/kanwia-ai/flightfinder.git
cd flightfinder
pip install -e .
```

Set your SerpAPI key:
```bash
export FLIGHTFINDER_SERPAPI_KEY="your-api-key"
```

Get an API key at [serpapi.com](https://serpapi.com/)

## Usage

### Quick Search

```bash
# One-way flight
flightfinder quick JFK NSI 2025-03-15

# Round trip
flightfinder quick JFK NSI 2025-03-15 2025-03-25

# Multiple origins (compare DC area airports)
flightfinder quick IAD,DCA,BWI NSI 2025-12-14 2026-01-01

# JSON output for automation
flightfinder quick BWI NSI 2025-12-14 2026-01-01 --json
```

### Interactive Search

```bash
flightfinder search
```

Guides you through all search options including cabin class, max stops, price limits, and preferred airlines.

### Export n8n Monitor

```bash
flightfinder monitor export \
  --name "cameroon-flights" \
  --from IAD,DCA,BWI \
  --to NSI \
  --depart 2025-03-15 \
  --return 2025-03-25 \
  --alert-below 1500
```

Generates an n8n workflow JSON that monitors prices daily and alerts when they drop below your threshold.

## Output Example

```
                                    Flight Results
┏━━━━┳━━━━━━━━┳━━━━━━━━━━━━━━━━━━━┳━━━━━━━━━━━━┳━━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━━┳━━━━━━━━━┳━━━━━━━━━━━━━┓
┃  # ┃  Price ┃ Airline           ┃ Route      ┃ Depart        ┃ Arrive        ┃  Stops  ┃ Layovers    ┃
┡━━━━╇━━━━━━━━╇━━━━━━━━━━━━━━━━━━━╇━━━━━━━━━━━━╇━━━━━━━━━━━━━━━╇━━━━━━━━━━━━━━━╇━━━━━━━━━╇━━━━━━━━━━━━━┩
│  1 │ $1,954 │ United, Brussels  │ BWI → NSI  │ Dec 14 13:10  │ Dec 15 17:45  │ 2 stops │ ORD → BRU   │
│  2 │ $2,265 │ Delta, Air France │ IAD → NSI  │ Dec 14 19:50  │ Dec 15 18:30  │ 2 stops │ ATL → CDG   │
│  3 │ $2,369 │ United, Brussels  │ BWI → NSI  │ Dec 14 17:18  │ Dec 15 17:45  │ 3 stops │ ORD → EWR → BRU │
└────┴────────┴───────────────────┴────────────┴───────────────┴───────────────┴─────────┴─────────────┘
```

## Development

```bash
# Install dev dependencies
pip install -e ".[dev]"

# Run tests (109 tests, 85% coverage)
pytest

# Run with coverage
pytest --cov=flightfinder

# Lint
ruff check flightfinder/
```

## Project Structure

```
flightfinder/
├── api/
│   └── serpapi.py      # SerpAPI client for Google Flights
├── cli.py              # Click CLI commands
├── compare.py          # Price comparison and filtering
├── config.py           # Environment configuration
├── export.py           # n8n workflow JSON generation
├── interactive.py      # Interactive search prompts
├── models.py           # Data models (FlightLeg, FlightOption, etc.)
├── output.py           # Rich terminal output formatting
└── search.py           # Search orchestration across origins
```

## License

MIT

---

*Built with [Claude Code](https://claude.com/claude-code)*
