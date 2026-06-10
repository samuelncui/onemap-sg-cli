# onemap-sg-cli

CLI for Singapore OneMap APIs. Run via `uvx onemap-sg-cli` (no install needed).

Output: `-f text` (default, readable), `-f json` (simplified), `-f raw-json` (full).

## Setup (one-time)

```bash
cat > ~/.onemap.env << 'EOF'
ONEMAP_EMAIL=your@email.com
ONEMAP_EMAIL_PASSWORD=your_password
EOF
```

Register: https://www.onemap.gov.sg/apidocs/register

## Search

```bash
uvx onemap-sg-cli search "Orchard Road"
uvx onemap-sg-cli search "307987"          # postal code
```

## Geocode

```bash
uvx onemap-sg-cli geocode wgs84 1.342 103.732
uvx onemap-sg-cli geocode svy21 16790 36056
```

## Routing

**Transit** — addresses, postal codes, or `lat,lon`:

```bash
uvx onemap-sg-cli route transit "Chinese Garden MRT" "One Raffles Quay"
uvx onemap-sg-cli route transit "1.342,103.732" "1.281,103.852"
uvx onemap-sg-cli route transit "Chinese Garden MRT" "One Raffles Quay" --time "09:00"
uvx onemap-sg-cli route transit "Chinese Garden MRT" "One Raffles Quay" --mode RAIL
```

`--time`: RFC 3339 (`"09:00"`, `"2026-06-08T09:00:00+08:00"`) or Unix timestamp.  
`--mode`: `TRANSIT` (default), `RAIL`, `BUS`.  
`--num`: 1-3 itineraries (default 1).

**Walk / Drive / Cycle:**

```bash
uvx onemap-sg-cli route walk "Chinese Garden MRT" "Jurong East MRT"
uvx onemap-sg-cli route drive "1.342,103.732" "1.281,103.852"
```

## Convert

```bash
uvx onemap-sg-cli convert wgs84-to-svy21 1.342 103.732
uvx onemap-sg-cli convert svy21-to-wgs84 16790 36056
uvx onemap-sg-cli convert wgs84-to-mercator 1.342 103.732
uvx onemap-sg-cli convert svy21-to-mercator 16790 36056
uvx onemap-sg-cli convert mercator-to-svy21 11546000 160000
uvx onemap-sg-cli convert mercator-to-wgs84 11546000 160000
```

## Themes

```bash
uvx onemap-sg-cli theme list
uvx onemap-sg-cli theme list --detail
uvx onemap-sg-cli theme get kindergartens --extents "1.29,103.78,1.33,103.87"
```

## Planning Areas

```bash
uvx onemap-sg-cli planning names
uvx onemap-sg-cli planning locate 1.342 103.732
```

## Population

```bash
uvx onemap-sg-cli pop age Bedok 2020
uvx onemap-sg-cli pop ethnic Tampines 2020 --gender female
uvx onemap-sg-cli pop income Bedok 2020
```

Subcommands: `age`, `economic`, `education`, `ethnic`, `income-hh`, `size-hh`, `structure-hh`, `income`, `industry`, `language-lit`, `marital`, `transport-school`, `transport-work`, `religion`, `language-home`, `tenancy`, `dwelling-hh`, `dwelling-pop`.  
Years: 2000, 2010, 2015, 2020.

## Nearby

```bash
uvx onemap-sg-cli nearby mrt 1.342 103.732 --radius 2000
uvx onemap-sg-cli nearby bus 1.342 103.732
```

## Amenities

```bash
uvx onemap-sg-cli amenity nearby 1.342 103.732 hawker_centres --radius 1000
```

Types: `hawker_centres`, `kindergartens`, `childcare`, `community_clubs`, `parks`, `nparks`, `hospitals`, `polyclinics`, `libraries`, `sports_facilities`, `eldercare`, `heritage_trees`, `monuments`, `hotels`.

## Map

```bash
uvx onemap-sg-cli map default --lat 1.342 --lon 103.732 -o map.png
uvx onemap-sg-cli map night --postal 609959 -o map.png
```

Layers: `default`, `night`, `grey`, `original`, `landlot`. Zoom 11-19. Size 128-512px.

## Elevation

```bash
uvx onemap-sg-cli elevation point 1.352 103.820
uvx onemap-sg-cli elevation profile "1.35,103.82|1.36,103.83"
```

## URA Property (needs URA_ACCESS_KEY)

```bash
uvx onemap-sg-cli ura transactions --batch 1
uvx onemap-sg-cli ura median-rentals
uvx onemap-sg-cli ura carpark-avail
uvx onemap-sg-cli ura carpark-details
```

Key: https://www.ura.gov.sg/maps/api/
