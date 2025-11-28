# FlightFinder

CLI tool to find the cheapest flights from multiple origin airports with n8n integration for automated price monitoring.

## Features

- **Multi-origin search** - Compare prices from multiple airports (e.g., all DC area airports)
- **Flexible dates** - Search across date ranges to find the best deals
- **Smart filtering** - Filter by stops, price, airlines, layover times
- **Rich output** - Beautiful terminal tables with airline, arrival time, and layover info
- **JSON export** - Machine-readable output for automation
- **n8n integration** - Export monitors as n8n workflows for automated alerts

## Installation

```bash
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
# One-way
flightfinder quick JFK NSI 2025-03-15

# Round trip
flightfinder quick JFK NSI 2025-03-15 2025-03-25

# Multiple origins
flightfinder quick IAD,DCA,BWI NSI 2025-03-15 2025-03-25
```

### Interactive Search

```bash
flightfinder search
```

Guides you through all search options including cabin class, max stops, and price limits.

### Export n8n Monitor

```bash
flightfinder monitor export \
  --name "cameroon-march" \
  --from IAD,DCA,BWI \
  --to NSI \
  --depart 2025-03-15 \
  --return 2025-03-25 \
  --alert-below 1500
```

Generates an n8n workflow JSON that monitors prices and alerts when they drop below your threshold.

## Output Example

```
                              Flight Results
┏━━━━┳━━━━━━━━┳━━━━━━━━━━━━━━━━━┳━━━━━━━━━━━━┳━━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━━┳━━━━━━━━━┳━━━━━━━━━━━━━┓
┃  # ┃  Price ┃ Airline         ┃ Route      ┃ Depart        ┃ Arrive        ┃  Stops  ┃ Layovers    ┃
┡━━━━╇━━━━━━━━╇━━━━━━━━━━━━━━━━━╇━━━━━━━━━━━━╇━━━━━━━━━━━━━━━╇━━━━━━━━━━━━━━━╇━━━━━━━━━╇━━━━━━━━━━━━━┩
│  1 │ $1,954 │ United, Brussels│ BWI → NSI  │ Dec 14 13:10  │ Dec 15 17:45  │ 2 stops │ ORD → BRU   │
│  2 │ $2,265 │ Delta, Air France│ IAD → NSI │ Dec 14 19:50  │ Dec 15 18:30  │ 2 stops │ ATL → CDG   │
└────┴────────┴─────────────────┴────────────┴───────────────┴───────────────┴─────────┴─────────────┘
```

## Development

```bash
# Install dev dependencies
pip install -e ".[dev]"

# Run tests
pytest

# Run with coverage
pytest --cov=flightfinder
```

## License

MIT

---

🤖 Generated with [Claude Code](https://claude.com/claude-code)
