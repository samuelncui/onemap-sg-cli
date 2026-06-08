# onemap-sg-cli

CLI for Singapore OneMap APIs. Run via `uvx` (no install needed) or `pip install onemap-sg-cli`.

## Setup

```bash
# Create credential file (one-time)
cat > ~/.onemap.env << 'EOF'
ONEMAP_EMAIL=your@email.com
ONEMAP_EMAIL_PASSWORD=your_password
EOF

# Load before use
export $(cat ~/.onemap.env | xargs)
```

Register: https://www.onemap.gov.sg/apidocs/register

## Usage

Prefix: `uvx --from onemap-sg-cli onemap`

### Search
```bash
uvx --from onemap-sg-cli onemap search "Orchard Road"
uvx --from onemap-sg-cli onemap search "307987"
```

### Routing — accepts address, postal code, or lat,lon
```bash
uvx --from onemap-sg-cli onemap route transit "Chinese Garden MRT" "One Raffles Quay"
uvx --from onemap-sg-cli onemap route transit "1.342,103.732" "1.281,103.852"
uvx --from onemap-sg-cli onemap route transit "Chinese Garden MRT" "One Raffles Quay" --time "09:00"
uvx --from onemap-sg-cli onemap route walk "Chinese Garden MRT" "Jurong East MRT"
```

`--time` accepts RFC 3339 (`"09:00"`, `"2026-06-08T09:00:00+08:00"`) or Unix timestamp.

### Geocode
```bash
uvx --from onemap-sg-cli onemap geocode wgs84 1.342 103.732
```

### Coordinate conversion
```bash
uvx --from onemap-sg-cli onemap convert wgs84-to-svy21 1.342 103.732
```

### Demographics
```bash
uvx --from onemap-sg-cli onemap pop age Bedok 2020
uvx --from onemap-sg-cli onemap pop ethnic Tampines 2020 --gender female
```

### Nearby transport
```bash
uvx --from onemap-sg-cli onemap nearby mrt 1.342 103.732 --radius 2000
```

### Amenities
```bash
uvx --from onemap-sg-cli onemap amenity nearby 1.342 103.732 hawker_centres --radius 1000
```

### Map
```bash
uvx --from onemap-sg-cli onemap map default --lat 1.342 --lon 103.732 -o map.png
```

### URA property data (needs URA_ACCESS_KEY)
```bash
uvx --from onemap-sg-cli onemap ura transactions --batch 1
uvx --from onemap-sg-cli onemap ura median-rentals
```

## Notes

- All route commands auto-geocode addresses via OneMap search
- If credentials missing, CLI exits with error — create `~/.onemap.env`
- URA data requires separate `URA_ACCESS_KEY` from https://www.ura.gov.sg/maps/api/
- Pop years: 2000, 2010, 2015, 2020 only
- Map outputs base64 PNG; use `-o file.png` to save
