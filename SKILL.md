---
name: onemap-sg-cli
description: Singapore OneMap CLI — search, geocode, routing, themes, population data, and more. Use when the user needs Singapore address search, route planning, nearby amenities, demographic data, or map generation.
category: devops
---

# onemap-sg-cli

CLI for Singapore OneMap APIs. Run via `uvx onemap-sg-cli` (no install) or `pip install onemap-sg-cli`.

Output: `-f text` (default, readable), `-f json` (simplified), `-f raw-json` (full API response).

## Auth

Credentials are auto-loaded from `~/.onemap.env` (created once, persistent).

**If the CLI errors with "credentials not found"**, guide the user:

```bash
cat > ~/.onemap.env << 'EOF'
ONEMAP_EMAIL=your@email.com
ONEMAP_EMAIL_PASSWORD=your_password
EOF
```

Register: https://www.onemap.gov.sg/apidocs/register  
URA data: add `URA_ACCESS_KEY` — https://www.ura.gov.sg/maps/api/

## Commands

All examples use `uvx onemap-sg-cli`. If pip-installed, replace with `onemap`.

### search — Address / building / postal code

```bash
uvx onemap-sg-cli search "Orchard Road"
uvx onemap-sg-cli search "307987"
uvx onemap-sg-cli search "Chinese Garden MRT"
```

### geocode — Coordinates → address

```bash
uvx onemap-sg-cli geocode wgs84 1.342 103.732
uvx onemap-sg-cli geocode wgs84 1.342 103.732 --hdb
uvx onemap-sg-cli geocode svy21 16790 36056
```

### route transit — Public transport

Accepts addresses, postal codes, or `lat,lon`:

```bash
uvx onemap-sg-cli route transit "Chinese Garden MRT" "One Raffles Quay"
uvx onemap-sg-cli route transit "1.342,103.732" "1.281,103.852"
uvx onemap-sg-cli route transit "609959" "048583"

# Options
uvx onemap-sg-cli route transit "Chinese Garden MRT" "One Raffles Quay" --time "09:00"
uvx onemap-sg-cli route transit "Chinese Garden MRT" "One Raffles Quay" --time "2026-06-08T09:00:00+08:00"
uvx onemap-sg-cli route transit "Chinese Garden MRT" "One Raffles Quay" --time "1780966800"
uvx onemap-sg-cli route transit "Chinese Garden MRT" "One Raffles Quay" --mode RAIL
uvx onemap-sg-cli route transit "Chinese Garden MRT" "One Raffles Quay" --mode BUS
```

`--time`: RFC 3339 or Unix timestamp. No separate `--date`.  
`--mode`: `TRANSIT` (default), `RAIL`, `BUS`.  
`--num`: 1-3 itineraries (default 1).  
`--max-walk`: limit walking distance in meters.

### route walk / drive / cycle

```bash
uvx onemap-sg-cli route walk "Chinese Garden MRT" "Jurong East MRT"
uvx onemap-sg-cli route drive "1.342,103.732" "1.281,103.852"
uvx onemap-sg-cli route cycle "1.342,103.732" "1.281,103.852"
```

### convert — Coordinate conversion

```bash
uvx onemap-sg-cli convert wgs84-to-svy21 1.342 103.732
uvx onemap-sg-cli convert svy21-to-wgs84 16790 36056
uvx onemap-sg-cli convert wgs84-to-mercator 1.342 103.732
uvx onemap-sg-cli convert svy21-to-mercator 16790 36056
uvx onemap-sg-cli convert mercator-to-svy21 11546000 160000
uvx onemap-sg-cli convert mercator-to-wgs84 11546000 160000
```

### theme — Thematic layers

```bash
uvx onemap-sg-cli theme list
uvx onemap-sg-cli theme list --detail
uvx onemap-sg-cli theme info kindergartens
uvx onemap-sg-cli theme get kindergartens --extents "1.29,103.78,1.33,103.87"
```

### planning — Planning areas

```bash
uvx onemap-sg-cli planning names
uvx onemap-sg-cli planning names --year 2019
uvx onemap-sg-cli planning locate 1.342 103.732
```

### pop — Demographics

```bash
uvx onemap-sg-cli pop age Bedok 2020
uvx onemap-sg-cli pop age Bedok 2020 --gender female
uvx onemap-sg-cli pop ethnic Tampines 2020
uvx onemap-sg-cli pop income Bedok 2020
```

Subcommands: `age`, `economic`, `education`, `ethnic`, `income-hh`, `size-hh`, `structure-hh`, `income`, `industry`, `language-lit`, `marital`, `transport-school`, `transport-work`, `religion`, `language-home`, `tenancy`, `dwelling-hh`, `dwelling-pop`.  
Years: 2000, 2010, 2015, 2020.

### nearby — Nearby transport

```bash
uvx onemap-sg-cli nearby mrt 1.342 103.732 --radius 2000
uvx onemap-sg-cli nearby bus 1.342 103.732
```

### amenity — Nearby amenities

```bash
uvx onemap-sg-cli amenity nearby 1.342 103.732 hawker_centres --radius 1000
```

Types: `hawker_centres`, `kindergartens`, `childcare`, `community_clubs`, `parks`, `nparks`, `hospitals`, `polyclinics`, `libraries`, `sports_facilities`, `eldercare`, `heritage_trees`, `monuments`, `hotels`.

### map — Static map

```bash
uvx onemap-sg-cli map default --lat 1.342 --lon 103.732 -o map.png
uvx onemap-sg-cli map night --postal 609959 -o map.png
```

Layers: `default`, `night`, `grey`, `original`, `landlot`. Zoom: 11-19. Size: 128-512px.

### elevation — Terrain height

```bash
uvx onemap-sg-cli elevation point 1.352 103.820
uvx onemap-sg-cli elevation profile "1.35,103.82|1.36,103.83"
```

### ura — URA property data

Needs `URA_ACCESS_KEY` in `~/.onemap.env`.

```bash
uvx onemap-sg-cli ura transactions --batch 1
uvx onemap-sg-cli ura rentals --period 25q1
uvx onemap-sg-cli ura median-rentals
uvx onemap-sg-cli ura developer-sales --period 0925
uvx onemap-sg-cli ura pipeline
uvx onemap-sg-cli ura decisions --year 2025
uvx onemap-sg-cli ura carpark-avail
uvx onemap-sg-cli ura carpark-details
```

## Pitfalls

1. **Auth**: create `~/.onemap.env` once. CLI auto-loads it.
2. **Route addresses**: `"Chinese Garden MRT"`, `"609959"`, `"1.342,103.732"` all work.
3. **`--time`**: RFC 3339 or Unix timestamp. No separate `--date`.
4. **Route default**: 1 itinerary (fast). Use `--num 3` for alternatives.
5. **Output format**: `-f text` (default), `-f json`, `-f raw-json`.
6. **URA**: needs `URA_ACCESS_KEY` in `~/.onemap.env`.
7. **Map**: base64 PNG in JSON. Use `-o file.png` to save.

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
