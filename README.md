# onemap-sg-cli

CLI and Python library for [OneMap Singapore](https://www.onemap.gov.sg/) APIs — search, geocode, routing, thematic layers, demographics, and URA property data.

## Install

```bash
pip install onemap-sg-cli
```

Or with pipx:

```bash
pipx install onemap-sg-cli
```

Or with uvx (no install needed):

```bash
uvx onemap-sg-cli search "Orchard Road"
```

## Setup

Set environment variables (or create a `.env` file):

```bash
export ONEMAP_EMAIL="your@email.com"
export ONEMAP_EMAIL_PASSWORD="your_password"

# Optional: URA property data
export URA_ACCESS_KEY="your_ura_key"
```

Get credentials:
- OneMap: https://www.onemap.gov.sg/apidocs/register
- URA: https://www.ura.gov.sg/maps/api/

## CLI Usage

```bash
# Search
onemap search "Orchard Road"

# Route finding — accepts addresses, postal codes, or lat,lon
onemap route transit "Chinese Garden MRT" "One Raffles Quay"
onemap route transit "Chinese Garden MRT" "One Raffles Quay" --time "09:00"

# Coordinate conversion
onemap convert wgs84-to-svy21 1.342 103.732

# Demographics
onemap pop age "Bedok" 2020

# Nearby transport
onemap nearby mrt 1.342 103.732 --radius 2000

# Static map
onemap map default --lat 1.342 --lon 103.732 -o map.png
```

See `onemap --help` for all commands.

## Python Library

```python
import asyncio
import onemap_sg

result = asyncio.run(onemap_sg.search("Orchard Road"))
route = asyncio.run(onemap_sg.route_public_transport(
    1.342, 103.732, 1.281, 103.852,
    departure_time="2026-06-08T09:00:00+08:00", mode="TRANSIT",
))
```

## Hermes Skill / Agent Instructions

One-line install for any AI agent:

```bash
# Hermes
curl -sSL https://raw.githubusercontent.com/samuelncui/onemap-sg-cli/main/install-agent.sh | bash -s hermes

# Cursor
curl -sSL https://raw.githubusercontent.com/samuelncui/onemap-sg-cli/main/install-agent.sh | bash -s cursor

# Claude Code
curl -sSL https://raw.githubusercontent.com/samuelncui/onemap-sg-cli/main/install-agent.sh | bash -s claude

# Universal (AGENTS.md)
curl -sSL https://raw.githubusercontent.com/samuelncui/onemap-sg-cli/main/install-agent.sh | bash -s agents
```

Supported: `hermes`, `cursor`, `claude`, `cline`, `copilot`, `windsurf`, `aider`, `agents`.

## License

MIT
