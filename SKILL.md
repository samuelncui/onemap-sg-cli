---
name: onemap-sg-cli
description: Singapore OneMap CLI — search, geocode, routing, themes, population data, and more. Use when the user needs Singapore address search, route planning, nearby amenities, demographic data, or map generation.
category: devops
---

# onemap-sg-cli

CLI for Singapore OneMap APIs. Run via `uvx onemap-sg-cli` (no install) or `pip install onemap-sg-cli`.

## Auth

Credentials are auto-loaded from `~/.onemap.env` (created once, persistent).

**If the CLI errors with "credentials not found"**, guide the user:

```bash
cat > ~/.onemap.env << 'EOF'
ONEMAP_EMAIL=your@email.com
ONEMAP_EMAIL_PASSWORD=your_password
EOF
```

Register: https://www.onemap.gov.sg/apidocs/register. URA data needs `URA_ACCESS_KEY` from https://www.ura.gov.sg/maps/api/. No env-var exporting needed — the CLI auto-loads `~/.onemap.env`.

## Commands

All examples use `uvx onemap-sg-cli`. If pip-installed, replace with `onemap`.

### Search
```bash
uvx onemap-sg-cli search "Orchard Road"
uvx onemap-sg-cli search "307987"
```

### Geocode
```bash
uvx onemap-sg-cli geocode wgs84 1.342 103.732
```

### Routing
```bash
# Walk / Drive / Cycle
uvx onemap-sg-cli route walk "Chinese Garden MRT" "Jurong East MRT"

# Public transport — address, postal, or lat,lon
uvx onemap-sg-cli route transit "Chinese Garden MRT" "One Raffles Quay"
uvx onemap-sg-cli route transit "1.342,103.732" "1.281,103.852"
uvx onemap-sg-cli route transit "Chinese Garden MRT" "One Raffles Quay" --time "09:00"
```

### Coordinate Conversion
```bash
uvx onemap-sg-cli convert wgs84-to-svy21 1.342 103.732
```

### Demographics
```bash
uvx onemap-sg-cli pop age Bedok 2020
```

### Nearby Transport
```bash
uvx onemap-sg-cli nearby mrt 1.342 103.732 --radius 2000
```

### Static Map
```bash
uvx onemap-sg-cli map default --lat 1.342 --lon 103.732 --zoom 15 -o map.png
```

### Full help
```bash
uvx onemap-sg-cli --help
```

## Pitfalls

1. **Auth**: create `~/.onemap.env` once. CLI auto-loads it. No env vars needed.
2. **Route addresses**: auto-geocoded. `"Chinese Garden MRT"`, `"609959"`, `"1.342,103.732"` all work.
3. **`--time` format**: RFC 3339 (`"09:00"`, `"2026-06-08T09:00:00+08:00"`) or Unix timestamp (`"1780966800"`). No separate `--date`.
4. **URA**: needs `URA_ACCESS_KEY` in `~/.onemap.env`.
5. **Static map**: base64 PNG in JSON. Use `-o file.png` to save.

## Python Library

```python
import asyncio, onemap_sg

result = asyncio.run(onemap_sg.search("Orchard Road"))
route = asyncio.run(onemap_sg.route_public_transport(
    1.342, 103.732, 1.281, 103.852,
    departure_time="2026-06-08T09:00:00+08:00", mode="TRANSIT",
))
```

## One-line install

```bash
curl -sSL https://raw.githubusercontent.com/samuelncui/onemap-sg-cli/main/install-agent.sh | bash
```
