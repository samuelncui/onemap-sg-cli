# onemap-sg-cli

CLI and Python library for [OneMap Singapore](https://www.onemap.gov.sg/) APIs — search, geocode, routing, thematic layers, demographics, and URA property data.

## Install

```bash
pip install onemap-sg-cli
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
onemap search "307987"              # postal code

# Geocode
onemap geocode wgs84 1.342 103.732
onemap geocode svy21 16790 36056

# Routing
onemap route walk 1.342 103.732 1.281 103.852
onemap route drive 1.342 103.732 1.281 103.852
onemap route transit 1.342 103.732 1.281 103.852

# Coordinate conversion
onemap convert wgs84-to-svy21 1.342 103.732
onemap convert svy21-to-wgs84 16790 36056

# Themes
onemap theme list
onemap theme get kindergartens --extents "1.29,103.78,1.33,103.87"

# Planning areas
onemap planning names
onemap planning locate 1.342 103.732

# Demographics
onemap pop age "Bedok" 2020
onemap pop ethnic "Tampines" 2020 --gender female

# Nearby transport
onemap nearby mrt 1.342 103.732 --radius 2000
onemap nearby bus 1.342 103.732

# Amenities
onemap amenity nearby 1.342 103.732 hawker_centres

# Static map
onemap map default --lat 1.342 --lon 103.732 -o map.png

# Elevation
onemap elevation point 1.352 103.820

# URA property data
onemap ura transactions --batch 1
onemap ura median-rentals
onemap ura carpark-avail
```

## Python Library

```python
import asyncio
import onemap_sg

# Search
result = asyncio.run(onemap_sg.search("Orchard Road"))

# Route
route = asyncio.run(onemap_sg.route_public_transport(
    1.342, 103.732, 1.281, 103.852,
    date="06-08-2026", departure_time="090000", mode="TRANSIT",
))

# Demographics
pop = asyncio.run(onemap_sg.get_population_age_group("Bedok", 2020))
```

All functions return `dict` (raw API JSON). See `onemap --help` for the full command list.

## License

MIT
