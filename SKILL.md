---
name: onemap-sg-cli
description: Singapore OneMap CLI — search, geocode, routing, themes, population data, and more. Use when the user needs Singapore address search, route planning, nearby amenities, demographic data, or map generation.
category: devops
---

# onemap-sg-cli

CLI for Singapore OneMap APIs. Install: `pip install onemap-sg-cli`.

## Auth Setup

The CLI reads credentials from a `.env` file (auto-loaded by python-dotenv).

Create `~/.onemap.env`:

```bash
cat > ~/.onemap.env << 'EOF'
ONEMAP_EMAIL=your@email.com
ONEMAP_EMAIL_PASSWORD=your_password
# Optional: URA property data
URA_ACCESS_KEY=your_ura_key
EOF
```

Then source it or export:

```bash
export $(cat ~/.onemap.env | xargs)
# or add to ~/.bashrc / ~/.zshrc
```

Alternatively, create a `.env` in the current working directory — the CLI auto-loads it.

**If credentials are missing**, the CLI will error. Tell the user to:
1. Register at https://www.onemap.gov.sg/apidocs/register
2. Create `~/.onemap.env` with the credentials above
3. Export them or restart the shell

## Commands

### Search
```bash
onemap search "Orchard Road"
onemap search "307987"
```

### Geocode (coords → address)
```bash
onemap geocode wgs84 1.342 103.732
onemap geocode svy21 16790 36056
```

### Routing
```bash
# Walk / Drive / Cycle
onemap route walk "Chinese Garden MRT" "Jurong East MRT"

# Public transport — accepts address, postal, or lat,lon
onemap route transit "Chinese Garden MRT" "One Raffles Quay"
onemap route transit "1.342,103.732" "1.281,103.852"
onemap route transit "Chinese Garden MRT" "One Raffles Quay" --time "09:00"
onemap route transit "Chinese Garden MRT" "One Raffles Quay" --time "2026-06-08T09:00:00+08:00"
```

### Coordinate Conversion
```bash
onemap convert wgs84-to-svy21 1.342 103.732
onemap convert svy21-to-wgs84 16790 36056
```

### Themes
```bash
onemap theme list
onemap theme get kindergartens --extents "1.29,103.78,1.33,103.87"
```

### Planning Areas
```bash
onemap planning names
onemap planning locate 1.342 103.732
```

### Population
```bash
onemap pop age "Bedok" 2020
onemap pop ethnic "Tampines" 2020 --gender female
```

### Nearby Transport
```bash
onemap nearby mrt 1.342 103.732 --radius 2000
onemap nearby bus 1.342 103.732
```

### Amenities
```bash
onemap amenity nearby 1.342 103.732 hawker_centres --radius 1000
```

### Static Map
```bash
onemap map default --lat 1.342 --lon 103.732 --zoom 15 -o map.png
```

### Elevation
```bash
onemap elevation point 1.352 103.820
onemap elevation profile "1.35,103.82|1.36,103.83"
```

### URA Property Data
```bash
onemap ura transactions --batch 1
onemap ura median-rentals
onemap ura carpark-avail
```

## Pitfalls

1. **Auth persistence**: create `~/.onemap.env` with credentials. The CLI auto-loads `.env` from CWD or you can export env vars directly.
2. **Route accepts addresses**: `onemap route transit "Chinese Garden MRT" "One Raffles Quay"` — auto-geocodes. Also accepts `"lat,lon"` or postal codes.
3. **Route transit `--time`**: RFC 3339 or Unix timestamp. `"09:00"` (today), `"2026-06-08T09:00:00+08:00"` (full), `"1780966800"` (timestamp). No separate `--date`.
4. **URA requires separate key**: `URA_ACCESS_KEY` from https://www.ura.gov.sg/maps/api/.
5. **Elevation uses external API**: Open-Elevation, 30m SRTM resolution.
6. **Planning area / population years**: 2000, 2010, 2015, 2020 only.
7. **Static map**: returns base64 PNG in JSON; use `-o file.png` to save.

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
