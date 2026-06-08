---
name: onemap-sg-cli
description: Singapore OneMap CLI — search, geocode, routing, themes, population data, and more. Use when the user needs Singapore address search, route planning, nearby amenities, demographic data, or map generation.
category: devops
---

# onemap-sg-cli

CLI for Singapore OneMap APIs. Run directly via `uvx` (no install needed) or `pip install onemap-sg-cli`.

## Auth Setup

Credentials are read from a `.env` file (auto-loaded by python-dotenv).

Create `~/.onemap.env`:

```bash
cat > ~/.onemap.env << 'EOF'
ONEMAP_EMAIL=your@email.com
ONEMAP_EMAIL_PASSWORD=your_password
# Optional
URA_ACCESS_KEY=your_ura_key
EOF
```

Export before running:

```bash
export $(cat ~/.onemap.env | xargs)
```

Or add to `~/.bashrc` / `~/.zshrc` for persistence.

**If credentials are missing**, the CLI exits with an error. Guide the user to:
1. Register at https://www.onemap.gov.sg/apidocs/register
2. Create `~/.onemap.env`
3. Export env vars

**Usage pattern**: prefix every command with `export $(cat ~/.onemap.env | xargs) &&` if not exported, or load once at session start.

## Commands

All commands can be run as `onemap ...` (if pip-installed) or `uvx --from onemap-sg-cli onemap ...` (no install).

### Search
```bash
uvx --from onemap-sg-cli onemap search "Orchard Road"
uvx --from onemap-sg-cli onemap search "307987"
```

### Geocode
```bash
uvx --from onemap-sg-cli onemap geocode wgs84 1.342 103.732
```

### Routing
```bash
# Walk / Drive / Cycle
uvx --from onemap-sg-cli onemap route walk "Chinese Garden MRT" "Jurong East MRT"

# Public transport — address, postal, or lat,lon
uvx --from onemap-sg-cli onemap route transit "Chinese Garden MRT" "One Raffles Quay"
uvx --from onemap-sg-cli onemap route transit "1.342,103.732" "1.281,103.852"
uvx --from onemap-sg-cli onemap route transit "Chinese Garden MRT" "One Raffles Quay" --time "09:00"
uvx --from onemap-sg-cli onemap route transit "Chinese Garden MRT" "One Raffles Quay" --time "2026-06-08T09:00:00+08:00"
```

### Coordinate Conversion
```bash
uvx --from onemap-sg-cli onemap convert wgs84-to-svy21 1.342 103.732
```

### Demographics
```bash
uvx --from onemap-sg-cli onemap pop age "Bedok" 2020
```

### Nearby Transport
```bash
uvx --from onemap-sg-cli onemap nearby mrt 1.342 103.732 --radius 2000
```

### Static Map
```bash
uvx --from onemap-sg-cli onemap map default --lat 1.342 --lon 103.732 --zoom 15 -o map.png
```

### Full list
```bash
uvx --from onemap-sg-cli onemap --help
```

## Pitfalls

1. **Auth**: create `~/.onemap.env`, export env vars before running. CLI auto-loads `.env` from CWD.
2. **Route addresses**: auto-geocoded. `"Chinese Garden MRT"`, `"609959"`, `"1.342,103.732"` all work.
3. **`--time` format**: RFC 3339 (`"09:00"`, `"2026-06-08T09:00:00+08:00"`) or Unix timestamp (`"1780966800"`). No separate `--date`.
4. **URA**: needs `URA_ACCESS_KEY` from https://www.ura.gov.sg/maps/api/.
5. **Elevation**: Open-Elevation, 30m SRTM — not survey-grade.
6. **Population years**: 2000, 2010, 2015, 2020 only.
7. **Static map**: base64 PNG in JSON. Use `-o file.png` to save.

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
curl -sSL https://raw.githubusercontent.com/samuelncui/onemap-sg-cli/main/install-skill.sh | bash
```
