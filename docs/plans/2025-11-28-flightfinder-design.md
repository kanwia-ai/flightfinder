# FlightFinder Design Document

A CLI tool to find the cheapest flights from multiple origin airports, with skiplagged/hidden-city fare discovery, open-jaw comparison, and n8n-powered monitoring.

## Architecture Overview

```
┌─────────────────────────────────────────────────────────┐
│                     USER INTERFACE                       │
│  CLI (ad-hoc searches)    n8n (scheduled + alerts)      │
└─────────────────────┬───────────────────────────────────┘
                      │
┌─────────────────────▼───────────────────────────────────┐
│                   FLIGHT FINDER CORE                     │
│  - Search orchestrator                                   │
│  - Price comparison engine                               │
│  - Skiplagged route finder                              │
└─────────────────────┬───────────────────────────────────┘
                      │
┌─────────────────────▼───────────────────────────────────┐
│                    DATA LAYER                            │
│  SQLite: route cache, search history, price history     │
│  OpenFlights DB: airline routes (refreshed monthly)     │
└─────────────────────┬───────────────────────────────────┘
                      │
┌─────────────────────▼───────────────────────────────────┐
│                   EXTERNAL APIs                          │
│  SerpAPI (Google Flights)    Fallback: Amadeus/Sky      │
└─────────────────────────────────────────────────────────┘
```

## CLI Interface

### Modes

1. **Quick mode**: `flightfinder quick JFK YAO 2025-03-15 2025-03-25` - uses all defaults
2. **Interactive mode**: `flightfinder search` - prompts for all parameters
3. **Flag mode**: Full flags for scripting/n8n integration

### Interactive Mode Flow

```
$ flightfinder search

Origin airports (comma-separated): JFK, EWR, IAD
Destination: YAO
Search nearby airports within [skip]: 100km

Departure date (YYYY-MM-DD): 2025-03-15
Flexible ± days [0]: 3
Depart after [any]: 18:00
Arrive before [any]:

Return date (YYYY-MM-DD or 'oneway'): 2025-03-25
Return depart after [any]:
Return arrive before [any]: 14:00

Max stops [any]: 1
Max travel time [any]: 24h
Cabin [economy]:
Airlines to avoid [none]: Spirit, Frontier
Layover min [45m]: 1h
Layover max [any]: 4h
Avoid connections [none]:

Max price [any]: 1500
Alert if below [none]: 1200

Include skiplagged fares? [y/N]: y

Searching...
```

### Search Parameters

**Time constraints:**
- Departure time window (leave after X)
- Arrival time window (arrive before X)

**Flight preferences:**
- Max stops (0, 1, 2, any)
- Max total travel time
- Preferred airlines / airlines to avoid
- Cabin class (economy, premium, business)

**Layover preferences:**
- Min/max layover duration
- Avoid specific connection airports

**Price:**
- Max budget
- Alert threshold (notify when below $X)

## Search Logic

### 1. Expand Origins
- If `--nearby` specified, find airports within radius of destination
- User's specified origins remain as-is

### 2. Build Search Matrix
For each origin airport, search:
- Round-trip to destination
- Two one-ways to destination (potentially different airlines)
- Open-jaw combinations if nearby airports found

### 3. Skiplagged Discovery (if enabled)
- Query route cache: "What airlines fly FROM destination X?"
- Get list of onward cities (e.g., from Yaoundé: Libreville, Douala, Kinshasa)
- Search for flights to those cities
- Filter results: only keep flights that connect through destination X
- Compare: is the "hidden city" fare cheaper than flying direct?

### 4. Rank Results
- Normalize all options by total price
- Apply user filters (time, stops, airlines, etc.)
- Return top results sorted by price

## Data Layer

### SQLite Database

**1. `routes` (airline route cache)**
```
airline_code | origin | destination | last_updated
    AF       |  JFK   |    CDG      | 2025-01-15
    ET       |  YAO   |    ADD      | 2025-01-15
```
- Populated from OpenFlights database
- Refreshed monthly via `flightfinder update-routes`
- Used for skiplagged route discovery

**2. `searches` (search history)**
```
id | timestamp | origins | destination | depart | return | params_json
1  | 2025-01-20 | JFK,EWR | YAO | 2025-03-15 | 2025-03-25 | {...}
```
- Lets you re-run past searches
- `flightfinder history --searches` shows recent searches

**3. `prices` (price history)**
```
id | search_id | route | price | booking_type | airline | fetched_at
1  |     1     | JFK→YAO | 1247 | round-trip  | AF      | 2025-01-20
```
- Tracks prices over time for routes you've searched
- Enables "price dropped" alerts in n8n
- `flightfinder history --from JFK --to YAO` shows price trends

## n8n Monitoring & Alerts

### Workflow Structure

```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│  Schedule   │────▶│ Run CLI     │────▶│  Compare    │────▶│ Send Alert  │
│  Trigger    │     │  Search     │     │  to Threshold│     │ (if needed) │
└─────────────┘     └─────────────┘     └─────────────┘     └─────────────┘
     Daily              --json            Price < $X?         Email/Slack
```

### Saved Monitors

```bash
$ flightfinder monitor add --name "cameroon-march" \
    --from JFK,EWR,IAD --to YAO \
    --depart 2025-03-15 --return 2025-03-25 \
    --alert-below 1200

Monitor saved. Add to n8n with:
  flightfinder monitor export --name "cameroon-march" --format n8n
```

## API Integration

### Primary: SerpAPI (Google Flights)
- $50/mo for 5,000 searches
- Returns structured JSON with prices, times, airlines, layovers
- Handles multi-city and one-way searches

### API Call Estimates

| Your search | API calls needed |
|-------------|------------------|
| 3 origins, round-trip | 3 calls |
| 3 origins, round-trip + two one-ways | 9 calls |
| 3 origins + skiplagged (5 onward cities) | 3 + 15 = 18 calls |
| Add ±3 day flex | multiply by 7 |

### Rate Limiting Strategy
- Queue all searches, execute with 200ms delay between calls
- Cache results for 6 hours
- Skip cached routes when re-running same search

### Fallback
- Amadeus API (free tier: 2,000 calls/mo) as backup

### API Key Storage
- Environment variable `FLIGHTFINDER_SERPAPI_KEY`
- Or in `~/.config/flightfinder/config.yaml`

## Output Format

### Terminal Output (default)

```
$ flightfinder quick JFK YAO 2025-03-15 2025-03-25

✓ Searched 3 origins × 4 booking types × 6 skiplagged routes = 72 combinations

TOP 10 RESULTS (sorted by price)

 #  PRICE   TYPE          ROUTE                    OUTBOUND              RETURN                STOPS
 1  $1,043  skiplagged    JFK→YAO (via CDG)       Mar 15 18:30 → +1d    Mar 25 09:15 → +1d    1 / 1
 2  $1,187  two-oneways   EWR→YAO / YAO→JFK       Mar 15 22:10 → +1d    Mar 25 11:00 → +1d    1 / 1
 3  $1,203  round-trip    JFK→YAO                 Mar 15 17:45 → +1d    Mar 25 14:30 → +1d    1 / 1
 ...

Details for #1? [enter number or 'q']:
```

### Detail View

```
FLIGHT #1 - $1,043 (skiplagged)

⚠️  SKIPLAGGED: Book to Libreville, deplane in Yaoundé. No checked bags.

OUTBOUND - Mar 15
  JFK 18:30 → CDG 08:15+1 (Air France AF007) - 7h 45m
  CDG 10:30 → YAO 17:45    (Air France AF840) - 6h 15m
  [YAO 19:00 → LBV 20:15 - DO NOT BOARD]

RETURN - Mar 25
  YAO 09:15 → CDG 16:30 (Air France AF841) - 6h 15m
  CDG 18:45 → JFK 21:30 (Air France AF008) - 8h 45m

Opening in browser...
```

When user selects a flight, automatically opens Google Flights booking URL in browser.

### Other Output Formats
- `--json` for machine-readable output (n8n uses this)
- `--csv` for spreadsheet export

## Error Handling

**API failures:**
- Retry 3x with exponential backoff
- Fall back to Amadeus if SerpAPI fails
- Show cached results with warning if both fail

**No results found:**
- Suggest loosening constraints
- Show cheapest option even if it exceeds filters

**Skiplagged warnings:**
- Always show ⚠️ warning for hidden-city fares
- Remind: no checked bags, frequent flyer risks

**Invalid inputs:**
- Unknown airport code: suggest closest matches
- Invalid dates: prompt again

**Rate limits:**
- Warn when approaching API limit
- Prioritize cheapest-first origins

## Tech Stack

**Language:** Python 3.11+

**Dependencies:**
- Rich - terminal UI (tables, colors, prompts)
- httpx - async API calls
- Click - CLI framework
- sqlite3 - database (built-in)

## File Structure

```
flightfinder/
├── cli.py              # CLI entry point (click commands)
├── interactive.py      # Interactive mode prompts
├── search.py           # Search orchestrator
├── skiplagged.py       # Hidden-city route discovery
├── compare.py          # Price comparison & ranking
├── api/
│   ├── serpapi.py      # SerpAPI integration
│   └── amadeus.py      # Fallback API
├── db/
│   ├── database.py     # SQLite connection & queries
│   ├── routes.py       # Route cache operations
│   └── history.py      # Search/price history
├── models.py           # Data classes (Flight, Search, etc.)
├── config.py           # Config file loading
├── export.py           # n8n workflow export
└── data/
    └── openflights/    # Route database files
```

**Config location:** `~/.config/flightfinder/config.yaml`
**Database location:** `~/.local/share/flightfinder/flights.db`

## Testing Strategy

**Unit tests:**
- Route discovery logic
- Price comparison & ranking
- Input validation

**Integration tests:**
- Mock API responses, verify full search flow
- Database operations
- n8n export generates valid workflow JSON

**Test data:**
- Fixtures with sample API responses
- Known routes for skiplagged testing
