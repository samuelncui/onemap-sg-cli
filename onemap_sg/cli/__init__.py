"""
onemap CLI — command-line interface for Singapore OneMap APIs.

Usage::

    onemap search "Orchard Road"
    onemap route walk 1.342 103.732 1.281 103.852
    onemap route transit 1.342 103.732 1.281 103.852 --time 090000
"""

from __future__ import annotations

import asyncio
import json
import sys
from typing import Any

import click


def _run(async_fn):
    """Helper: run async function and print JSON result, exit 1 on error."""

    def wrapper(*args, **kwargs):
        try:
            result = asyncio.run(async_fn(*args, **kwargs))
        except Exception as exc:
            click.echo(json.dumps({"error": str(exc)}, indent=2), err=True)
            sys.exit(1)
        click.echo(json.dumps(result, indent=2, ensure_ascii=False))

    return wrapper


# ---------------------------------------------------------------------------
# Shared options
# ---------------------------------------------------------------------------

_lat = click.argument("latitude", type=float)
_lon = click.argument("longitude", type=float)
_lat_opt = click.option("--lat", "latitude", type=float, help="Latitude (WGS84)")
_lon_opt = click.option("--lon", "longitude", type=float, help="Longitude (WGS84)")


@click.group()
@click.version_option()
def main():
    """OneMap SG CLI — Singapore mapping, geocoding, routing, and demographics."""
    pass


# ===========================================================================
# search
# ===========================================================================


@main.command()
@click.argument("query")
@click.option("--page", type=int, default=None, help="Page number")
def search(query: str, page: int | None):
    """Search address / building / postal code."""
    from onemap_sg import search as _search

    _run(_search)(query, page_number=page)


# ===========================================================================
# geocode
# ===========================================================================


@main.group()
def geocode():
    """Reverse geocode: coordinates → address."""


@geocode.command("wgs84")
@click.argument("latitude", type=float)
@click.argument("longitude", type=float)
@click.option("--buffer", type=int, default=None, help="Radius in meters (0-500)")
@click.option("--hdb/--all", "hdb_only", default=None, help="HDB only?")
def geocode_wgs84(latitude: float, longitude: float, buffer: int | None, hdb_only: bool | None):
    """Reverse geocode from WGS84 lat/lon."""
    from onemap_sg import reverse_geocode_wgs84

    atype = "HDB" if hdb_only else ("All" if hdb_only is False else None)
    _run(reverse_geocode_wgs84)(latitude, longitude, buffer=buffer, address_type=atype)


@geocode.command("svy21")
@click.argument("x", type=float)
@click.argument("y", type=float)
@click.option("--buffer", type=int, default=None, help="Radius in meters (0-500)")
@click.option("--hdb/--all", "hdb_only", default=None, help="HDB only?")
def geocode_svy21(x: float, y: float, buffer: int | None, hdb_only: bool | None):
    """Reverse geocode from SVY21 X/Y."""
    from onemap_sg import reverse_geocode_svy21

    atype = "HDB" if hdb_only else ("All" if hdb_only is False else None)
    _run(reverse_geocode_svy21)(x, y, buffer=buffer, address_type=atype)


# ===========================================================================
# route
# ===========================================================================


async def _resolve_location(value: str) -> tuple[float, float]:
    """Resolve a location string to (lat, lon).

    Accepts ``"lat,lon"`` or an address/postal-code (geocoded via OneMap search).
    Must be called from within an async context.
    """
    if "," in value:
        parts = value.split(",", 1)
        try:
            return float(parts[0].strip()), float(parts[1].strip())
        except ValueError:
            pass  # fall through to geocode

    # Geocode
    from onemap_sg import search

    result = await search(value)
    results = result.get("results", [])
    if not results:
        raise click.ClickException(f"No results found for: {value}")
    r = results[0]
    lat = float(r.get("LATITUDE", 0))
    lon = float(r.get("LONGITUDE", 0))
    if lat == 0 and lon == 0:
        raise click.ClickException(f"No coordinates for: {value}")
    return lat, lon


@main.group()
def route():
    """Routing: walk, drive, cycle, transit."""


@route.command("walk")
@click.argument("start")
@click.argument("end")
def route_walk(start, end):
    """Walking route.  START/END: "lat,lon" or address/postal."""
    from onemap_sg import route_walk_drive_cycle

    async def _do():
        s_lat, s_lon = await _resolve_location(start)
        e_lat, e_lon = await _resolve_location(end)
        return await route_walk_drive_cycle(s_lat, s_lon, e_lat, e_lon, "walk")

    _run(_do)()


@route.command("drive")
@click.argument("start")
@click.argument("end")
def route_drive(start, end):
    """Driving route.  START/END: "lat,lon" or address/postal."""
    from onemap_sg import route_walk_drive_cycle

    async def _do():
        s_lat, s_lon = await _resolve_location(start)
        e_lat, e_lon = await _resolve_location(end)
        return await route_walk_drive_cycle(s_lat, s_lon, e_lat, e_lon, "drive")

    _run(_do)()


@route.command("cycle")
@click.argument("start")
@click.argument("end")
def route_cycle(start, end):
    """Cycling route.  START/END: "lat,lon" or address/postal."""
    from onemap_sg import route_walk_drive_cycle

    async def _do():
        s_lat, s_lon = await _resolve_location(start)
        e_lat, e_lon = await _resolve_location(end)
        return await route_walk_drive_cycle(s_lat, s_lon, e_lat, e_lon, "cycle")

    _run(_do)()


@route.command("transit")
@click.argument("start")
@click.argument("end")
@click.option("--time", "departure_time", default=None, help="RFC3339 or Unix timestamp: '09:00', '2026-06-08T09:00:00+08:00', or '1759381200' (default: now)")
@click.option("--mode", "transit_mode", default="TRANSIT", type=click.Choice(["TRANSIT", "BUS", "RAIL"]))
@click.option("--max-walk", type=int, default=None, help="Max walking distance (m)")
@click.option("--num", type=int, default=None, help="Number of itineraries (1-3)")
def route_transit(start, end, departure_time, transit_mode, max_walk, num):
    """Public transport route.  START/END: "lat,lon" or address/postal."""
    from datetime import datetime
    from onemap_sg import route_public_transport

    if departure_time is None:
        departure_time = datetime.now().strftime("%Y-%m-%dT%H:%M:%S")

    async def _do():
        s_lat, s_lon = await _resolve_location(start)
        e_lat, e_lon = await _resolve_location(end)
        return await route_public_transport(
            s_lat, s_lon, e_lat, e_lon,
            departure_time=departure_time, mode=transit_mode,
            max_walk_distance=max_walk, num_itineraries=num,
        )

    _run(_do)()


# ===========================================================================
# convert
# ===========================================================================


@main.group()
def convert():
    """Coordinate conversion between WGS84, SVY21, Web Mercator."""


for _cmd, _fn, _a1, _a2 in [
    ("wgs84-to-svy21", "convert_4326_to_3414", "latitude", "longitude"),
    ("wgs84-to-mercator", "convert_4326_to_3857", "latitude", "longitude"),
    ("svy21-to-wgs84", "convert_3414_to_4326", "x", "y"),
    ("svy21-to-mercator", "convert_3414_to_3857", "x", "y"),
    ("mercator-to-svy21", "convert_3857_to_3414", "x", "y"),
    ("mercator-to-wgs84", "convert_3857_to_4326", "x", "y"),
]:
    def _make_cmd(fn_name, a1, a2):
        @click.argument(a1, type=float)
        @click.argument(a2, type=float)
        def cmd(**kwargs):
            from onemap_sg import coordinate
            fn = getattr(coordinate, fn_name)
            _run(fn)(kwargs[a1], kwargs[a2])
        return cmd
    cmd = _make_cmd(_fn, _a1, _a2)
    cmd.__name__ = _cmd.replace("-", "_")
    convert.add_command(click.command(_cmd)(cmd))


# ===========================================================================
# theme
# ===========================================================================


@main.group()
def theme():
    """Thematic layers (amenities, boundaries, etc)."""


@theme.command("list")
@click.option("--detail/--no-detail", default=False, help="Include full details")
def theme_list(detail: bool):
    """List all available themes."""
    from onemap_sg import get_all_themes_info
    _run(get_all_themes_info)(more_info="Y" if detail else "N")


@theme.command("info")
@click.argument("query_name")
def theme_info(query_name: str):
    """Get info about a specific theme."""
    from onemap_sg import get_theme_info
    _run(get_theme_info)(query_name)


@theme.command("get")
@click.argument("query_name")
@click.option("--extents", default=None, help="Bbox: lat1,lon1,lat2,lon2")
def theme_get(query_name: str, extents: str | None):
    """Retrieve data for a theme."""
    from onemap_sg import retrieve_theme
    _run(retrieve_theme)(query_name, extents=extents)


# ===========================================================================
# planning
# ===========================================================================


@main.group()
def planning():
    """Planning areas."""


@planning.command("all")
@click.option("--year", type=int, default=None, help="Year (1998/2008/2014/2019)")
def planning_all(year: int | None):
    """List all planning areas with polygons."""
    from onemap_sg import get_all_planning_areas
    _run(get_all_planning_areas)(year=year)


@planning.command("names")
@click.option("--year", type=int, default=None, help="Year (1998/2008/2014/2019)")
def planning_names(year: int | None):
    """List planning area names."""
    from onemap_sg import get_planning_area_names
    _run(get_planning_area_names)(year=year)


@planning.command("locate")
@click.argument("latitude", type=float)
@click.argument("longitude", type=float)
@click.option("--year", type=int, default=None, help="Year (1998/2008/2014/2019)")
def planning_locate(latitude: float, longitude: float, year: int | None):
    """Which planning area contains these coordinates?"""
    from onemap_sg import get_planning_area_by_location
    _run(get_planning_area_by_location)(latitude, longitude, year=year)


# ===========================================================================
# population
# ===========================================================================


@main.group()
def pop():
    """Population & demographic queries."""


_pop_commands = {
    "age": "get_population_age_group",
    "economic": "get_economic_status",
    "education": "get_education_status",
    "ethnic": "get_ethnic_distribution",
    "income-hh": "get_household_monthly_income",
    "size-hh": "get_household_size",
    "structure-hh": "get_household_structure",
    "income": "get_income_from_work",
    "industry": "get_industry_of_population",
    "language-lit": "get_language_literacy",
    "marital": "get_marital_status",
    "transport-school": "get_mode_of_transport_school",
    "transport-work": "get_mode_of_transport_work",
    "religion": "get_religion_data",
    "language-home": "get_spoken_language_at_home",
    "tenancy": "get_tenancy_data",
    "dwelling-hh": "get_dwelling_type_household",
    "dwelling-pop": "get_dwelling_type_population",
}

for _cmd_name, _fn_name in _pop_commands.items():

    def _make_pop_cmd(fn_name):
        @click.argument("planning_area")
        @click.argument("year", type=int)
        @click.option("--gender", type=click.Choice(["male", "female"]), default=None)
        def cmd(planning_area, year, gender):
            from onemap_sg import population
            fn = getattr(population, fn_name)
            try:
                if gender is not None:
                    _run(fn)(planning_area, year, gender=gender)
                else:
                    _run(fn)(planning_area, year)
            except TypeError:
                _run(fn)(planning_area, year)

        return cmd

    cmd = _make_pop_cmd(_fn_name)
    cmd.__name__ = _cmd_name.replace("-", "_")
    pop.add_command(click.command(_cmd_name, help=f"{_cmd_name} distribution")(cmd))


# ===========================================================================
# transport
# ===========================================================================


@main.group()
def nearby():
    """Nearby transport: MRT stations, bus stops."""


@nearby.command("mrt")
@click.argument("latitude", type=float)
@click.argument("longitude", type=float)
@click.option("--radius", type=int, default=None, help="Radius in meters (1-5000)")
def nearby_mrt(latitude: float, longitude: float, radius: int | None):
    """Find nearby MRT/LRT stations."""
    from onemap_sg import get_nearby_mrt_stations
    _run(get_nearby_mrt_stations)(latitude, longitude, radius_in_meters=radius)


@nearby.command("bus")
@click.argument("latitude", type=float)
@click.argument("longitude", type=float)
@click.option("--radius", type=int, default=None, help="Radius in meters (1-5000)")
def nearby_bus(latitude: float, longitude: float, radius: int | None):
    """Find nearby bus stops."""
    from onemap_sg import get_nearby_bus_stops
    _run(get_nearby_bus_stops)(latitude, longitude, radius_in_meters=radius)


# ===========================================================================
# amenities
# ===========================================================================


@main.group()
def amenity():
    """Nearby amenities."""


@amenity.command("nearby")
@click.argument("latitude", type=float)
@click.argument("longitude", type=float)
@click.argument("type_", metavar="TYPE")
@click.option("--radius", type=float, default=1000, help="Radius in meters")
def amenity_nearby(latitude: float, longitude: float, type_: str, radius: float):
    """Find amenities near a location.

    TYPE: hawker_centres, kindergartens, childcare, community_clubs, parks,
    nparks, hospitals, polyclinics, libraries, sports_facilities,
    eldercare, heritage_trees, monuments, hotels"""
    from onemap_sg import get_nearby_amenities
    _run(get_nearby_amenities)(latitude, longitude, type_, radius_meters=radius)


# ===========================================================================
# map
# ===========================================================================


@main.command()
@click.argument("layer", type=click.Choice(["default", "night", "grey", "original", "landlot"]))
@click.option("--lat", type=float, default=None, help="Center latitude")
@click.option("--lon", type=float, default=None, help="Center longitude")
@click.option("--postal", default=None, help="Postal code (alternative to lat/lon)")
@click.option("--zoom", type=int, default=15, help="Zoom 11-19")
@click.option("--width", type=int, default=256, help="Width px (128-512)")
@click.option("--height", type=int, default=256, help="Height px (128-512)")
@click.option("--points", default=None, help="Point overlays")
@click.option("--lines", default=None, help="Line overlays")
@click.option("--polygons", default=None, help="Polygon overlays")
@click.option("--color", default=None, help="Line color R,G,B")
@click.option("--fill", "fill_color", default=None, help="Fill color R,G,B")
@click.option("--output", "-o", type=click.Path(), default=None, help="Save PNG to file")
def map_cmd(layer, lat, lon, postal, zoom, width, height, points, lines, polygons, color, fill_color, output):
    """Generate static map image (returns base64 PNG)."""
    from onemap_sg import get_static_map

    result = asyncio.run(get_static_map(
        layer_chosen=layer,
        zoom=zoom, width=width, height=height,
        latitude=lat, longitude=lon, postal=postal,
        points=points, lines=lines, polygons=polygons,
        color=color, fill_color=fill_color,
    ))

    if output and result.get("image_base64"):
        import base64
        with open(output, "wb") as f:
            f.write(base64.b64decode(result["image_base64"]))
        click.echo(f"Saved {output}")
    else:
        # Print without the base64 blob (too large)
        summary = {k: v for k, v in result.items() if k != "image_base64"}
        click.echo(json.dumps(summary, indent=2))


# ===========================================================================
# elevation
# ===========================================================================


@main.group()
def elevation():
    """Terrain elevation."""


@elevation.command("point")
@click.argument("latitude", type=float)
@click.argument("longitude", type=float)
def elevation_point(latitude: float, longitude: float):
    """Get elevation at a point."""
    from onemap_sg import get_elevation
    _run(get_elevation)(latitude, longitude)


@elevation.command("profile")
@click.argument("coordinates")
def elevation_profile(coordinates: str):
    """Get elevation profile: "lat1,lon1|lat2,lon2|..." """
    from onemap_sg import get_elevation_profile
    _run(get_elevation_profile)(coordinates)


# ===========================================================================
# ura
# ===========================================================================


@main.group()
def ura():
    """URA property & planning data."""


@ura.command("transactions")
@click.option("--batch", type=int, default=1, help="Batch 1-4 by district")
def ura_transactions(batch: int):
    """Private residential sales transactions (5yr)."""
    from onemap_sg.ura import get_private_residential_transactions
    _run(get_private_residential_transactions)(batch)


@ura.command("rentals")
@click.option("--period", default="25q4", help="Quarter in yyqq format")
def ura_rentals(period: str):
    """Private residential rental contracts."""
    from onemap_sg.ura import get_private_rental_contracts
    _run(get_private_rental_contracts)(period)


@ura.command("median-rentals")
def ura_median():
    """Median rentals (past 3 years)."""
    from onemap_sg.ura import get_median_rentals
    _run(get_median_rentals)()


@ura.command("developer-sales")
@click.option("--period", default="0925", help="Month in mmyy format")
def ura_dev_sales(period: str):
    """Developer sales (past 3 years)."""
    from onemap_sg.ura import get_developer_sales
    _run(get_developer_sales)(period)


@ura.command("pipeline")
def ura_pipeline():
    """Upcoming residential projects."""
    from onemap_sg.ura import get_residential_pipeline
    _run(get_residential_pipeline)()


@ura.command("decisions")
@click.option("--year", type=int, default=2025, help="Year (after 2000)")
def ura_decisions(year: int):
    """Planning decisions."""
    from onemap_sg.ura import get_planning_decisions
    _run(get_planning_decisions)(year)


@ura.command("carpark-avail")
def ura_carpark_avail():
    """Real-time car park availability."""
    from onemap_sg.ura import get_car_park_availability
    _run(get_car_park_availability)()


@ura.command("carpark-details")
def ura_carpark_details():
    """Car park list and rates."""
    from onemap_sg.ura import get_car_park_details
    _run(get_car_park_details)()
