# onemap-sg-cli

Singapore OneMap CLI — search, geocode, routing, themes, demographics, and URA property.  
Output: text (default), JSON (`-f json`), or raw API (`-f raw-json`).

## Install

```bash
pip install onemap-sg-cli          # global
pipx install onemap-sg-cli         # isolated
uvx onemap-sg-cli search "..."     # no install
```

## Setup

Create `~/.onemap.env` (auto-loaded, one-time):

```bash
cat > ~/.onemap.env << 'EOF'
ONEMAP_EMAIL=your@email.com
ONEMAP_EMAIL_PASSWORD=your_password
EOF
```

Register: https://www.onemap.gov.sg/apidocs/register  
URA data: add `URA_ACCESS_KEY` — https://www.ura.gov.sg/maps/api/

## Global Options

```
-f, --format [text|json|raw-json]   Output mode (default: text)
--version                           Show version
--help                              Show help
```

## Commands

### `search` — Address, building, postal code lookup

```bash
onemap search "Orchard Road"
onemap search "307987"                    # postal code
onemap search "Chinese Garden MRT"        # building
onemap search "Orchard" --page 2          # paginated
```

### `geocode` — Coordinates → address

```bash
onemap geocode wgs84 1.342 103.732        # WGS84 lat,lon
onemap geocode wgs84 1.342 103.732 --hdb   # HDB only
onemap geocode wgs84 1.342 103.732 --buffer 200
onemap geocode svy21 16790 36056          # SVY21 X,Y
```

### `route` — Directions

**Transit (bus + MRT)** — accepts addresses, postal codes, or `lat,lon`:

```bash
onemap route transit "Chinese Garden MRT" "One Raffles Quay"
onemap route transit "1.342,103.732" "1.281,103.852"
onemap route transit "609959" "048583"              # postal codes

# Options
onemap route transit ... --time "09:00"               # RFC 3339 time
onemap route transit ... --time "2026-06-08T09:00:00+08:00"
onemap route transit ... --time "1780966800"          # Unix timestamp
onemap route transit ... --mode RAIL                  # MRT/LRT only
onemap route transit ... --mode BUS                   # bus only
onemap route transit ... --max-walk 500               # limit walking
onemap route transit ... --num 3                      # more itineraries
```

**Walk / Drive / Cycle:**

```bash
onemap route walk "Chinese Garden MRT" "Jurong East MRT"
onemap route drive "1.342,103.732" "1.281,103.852"
onemap route cycle "1.342,103.732" "1.281,103.852"
```

### `convert` — Coordinate conversion

```bash
onemap convert wgs84-to-svy21 1.342 103.732
onemap convert svy21-to-wgs84 16790 36056
onemap convert wgs84-to-mercator 1.342 103.732
onemap convert svy21-to-mercator 16790 36056
onemap convert mercator-to-svy21 11546000 160000
onemap convert mercator-to-wgs84 11546000 160000
```

### `theme` — Thematic layers (100+ government datasets)

```bash
onemap theme list                            # all themes
onemap theme list --detail                   # with metadata
onemap theme info kindergartens              # specific theme info
onemap theme get kindergartens --extents "1.29,103.78,1.33,103.87"
```

### `planning` — Planning areas

```bash
onemap planning names                        # all area names
onemap planning names --year 2019
onemap planning all --year 2019              # with polygon boundaries
onemap planning locate 1.342 103.732         # which area contains this point?
```

### `pop` — Demographics by planning area

```bash
onemap pop age Bedok 2020
onemap pop age Bedok 2020 --gender female
onemap pop ethnic Tampines 2020
onemap pop income Bedok 2020
onemap pop religion Bedok 2020
onemap pop dwelling-hh Bedok 2020
```

All pop subcommands: `age`, `economic`, `education`, `ethnic`, `income-hh`, `size-hh`,
`structure-hh`, `income`, `industry`, `language-lit`, `marital`, `transport-school`,
`transport-work`, `religion`, `language-home`, `tenancy`, `dwelling-hh`, `dwelling-pop`.

Years: 2000, 2010, 2015, 2020.

### `nearby` — Nearby transport

```bash
onemap nearby mrt 1.342 103.732              # nearby MRT/LRT stations
onemap nearby mrt 1.342 103.732 --radius 500
onemap nearby bus 1.342 103.732              # nearby bus stops
```

### `amenity` — Nearby amenities

```bash
onemap amenity nearby 1.342 103.732 hawker_centres
onemap amenity nearby 1.342 103.732 hospitals --radius 2000
```

Types: `hawker_centres`, `kindergartens`, `childcare`, `community_clubs`, `parks`,
`nparks`, `hospitals`, `polyclinics`, `libraries`, `sports_facilities`, `eldercare`,
`heritage_trees`, `monuments`, `hotels`.

### `map` — Static map image

```bash
onemap map default --lat 1.342 --lon 103.732 -o map.png
onemap map night --lat 1.342 --lon 103.732 --zoom 17 --width 512 --height 512 -o map.png
onemap map original --postal 609959 -o map.png
```

Layers: `default`, `night`, `grey`, `original`, `landlot`. Zoom: 11-19. Size: 128-512px.

### `elevation` — Terrain height

```bash
onemap elevation point 1.352 103.820
onemap elevation profile "1.35,103.82|1.36,103.83|1.37,103.84"
```

Uses Open-Elevation (30m SRTM). Not survey-grade.

### `ura` — URA property & planning data

Needs `URA_ACCESS_KEY` in `~/.onemap.env`.

```bash
onemap ura transactions --batch 1            # private residential sales (5yr)
onemap ura rentals --period 25q1             # rental contracts
onemap ura median-rentals                    # median PSF rentals
onemap ura developer-sales --period 0925     # developer sales
onemap ura pipeline                          # upcoming projects
onemap ura decisions --year 2025             # planning decisions
onemap ura carpark-avail                     # real-time parking
onemap ura carpark-details                   # parking rates & info
```

## Output Formats

```
Default (text):        Duration: 33.5 min  |  Transfers: 0
                         Walk 22m
                         EW (CHINESE GARDEN → RAFFLES PLACE)
                         Walk 426m

-f json:               {"duration_min": 33.5, "transfers": 0, "legs": [...]}

-f raw-json:           {"requestParameters": {...}, "plan": {...}, ...}
```

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

## Agent Instructions

One-line install:

```bash
curl -sSL https://raw.githubusercontent.com/samuelncui/onemap-sg-cli/main/install-agent.sh | bash
```

Supported: `hermes`, `cursor`, `claude`, `cline`, `copilot`, `windsurf`, `aider`, `agents`.

## License

MIT
