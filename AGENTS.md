# onemap-sg-cli

CLI for Singapore OneMap APIs. Run via `uvx onemap-sg-cli` (no install needed).

## Setup (one-time)

```bash
cat > ~/.onemap.env << 'EOF'
ONEMAP_EMAIL=your@email.com
ONEMAP_EMAIL_PASSWORD=your_password
EOF
```

The CLI auto-loads `~/.onemap.env`. No env vars needed.
Register: https://www.onemap.gov.sg/apidocs/register

## Usage

```bash
# Search
uvx onemap-sg-cli search "Orchard Road"

# Transit routing — addresses, postal codes, or lat,lon
uvx onemap-sg-cli route transit "Chinese Garden MRT" "One Raffles Quay"
uvx onemap-sg-cli route transit "1.342,103.732" "1.281,103.852"
uvx onemap-sg-cli route transit "Chinese Garden MRT" "One Raffles Quay" --time "09:00"

# Walk
uvx onemap-sg-cli route walk "Chinese Garden MRT" "Jurong East MRT"

# Geocode
uvx onemap-sg-cli geocode wgs84 1.342 103.732

# Convert
uvx onemap-sg-cli convert wgs84-to-svy21 1.342 103.732

# Demographics
uvx onemap-sg-cli pop age Bedok 2020

# Nearby
uvx onemap-sg-cli nearby mrt 1.342 103.732 --radius 2000

# Amenities
uvx onemap-sg-cli amenity nearby 1.342 103.732 hawker_centres

# Map
uvx onemap-sg-cli map default --lat 1.342 --lon 103.732 -o map.png

# URA property (needs URA_ACCESS_KEY in ~/.onemap.env)
uvx onemap-sg-cli ura transactions --batch 1
```

## Notes

- `--time` accepts RFC 3339 (`"09:00"`, `"2026-06-08T09:00:00+08:00"`) or Unix timestamp
- Route commands auto-geocode addresses
- Pop years: 2000, 2010, 2015, 2020
- Map outputs base64 PNG; use `-o file.png`
