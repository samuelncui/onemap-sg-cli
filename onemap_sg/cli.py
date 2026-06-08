"""
onemap CLI — command-line interface for Singapore OneMap APIs.

Usage::

    onemap search "Orchard Road"
    onemap route transit "Chinese Garden MRT" "One Raffles Quay"
"""

from __future__ import annotations

import asyncio
import inspect
import json
import sys
from datetime import datetime
from typing import Any

import click


# ---------------------------------------------------------------------------
# Async Click support — single event loop across all commands
# ---------------------------------------------------------------------------


class AsyncCommand(click.Command):
    """Command that runs async callbacks via asyncio.run()."""

    def invoke(self, ctx: click.Context) -> Any:
        callback = ctx.command.callback  # type: ignore[union-attr]
        if inspect.iscoroutinefunction(callback):
            return asyncio.run(callback(**ctx.params))
        return super().invoke(ctx)


class AsyncGroup(click.Group):
    """Group that supports async subcommands."""

    command_class = AsyncCommand
    group_class = type


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


async def _resolve_location(value: str) -> tuple[float, float]:
    """Resolve a location string to (lat, lon).

    Accepts ``"lat,lon"`` or an address/postal-code (geocoded via OneMap search).
    """
    if "," in value:
        parts = value.split(",", 1)
        try:
            return float(parts[0].strip()), float(parts[1].strip())
        except ValueError:
            pass  # fall through to geocode

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


# ---------------------------------------------------------------------------
# CLI root
# ---------------------------------------------------------------------------


@click.group(cls=AsyncGroup)
@click.version_option()
def main():
    """OneMap SG CLI — Singapore mapping, geocoding, routing, and demographics."""


# ===========================================================================
# search
# ===========================================================================


@main.command(cls=AsyncCommand)
@click.argument("query")
@click.option("--page", type=int, default=None, help="Page number")
async def search(query: str, page: int | None):
    """Search address / building / postal code."""
    from onemap_sg import search as _search

    result = await _search(query, page_number=page)
    click.echo(json.dumps(result, indent=2, ensure_ascii=False))


# ===========================================================================
# geocode
# ===========================================================================


@main.group("geocode", cls=AsyncGroup)
def geocode():
    """Reverse geocode: coordinates → address."""


@geocode.command("wgs84", cls=AsyncCommand)
@click.argument("latitude", type=float)
@click.argument("longitude", type=float)
@click.option("--buffer", type=int, default=None, help="Radius in meters (0-500)")
@click.option("--hdb/--all", "hdb_only", default=None, help="HDB only?")
async def geocode_wgs84(latitude: float, longitude: float, buffer: int | None, hdb_only: bool | None):
    """Reverse geocode from WGS84 lat/lon."""
    from onemap_sg import reverse_geocode_wgs84

    atype = "HDB" if hdb_only else ("All" if hdb_only is False else None)
    result = await reverse_geocode_wgs84(latitude, longitude, buffer=buffer, address_type=atype)
    click.echo(json.dumps(result, indent=2, ensure_ascii=False))


@geocode.command("svy21", cls=AsyncCommand)
@click.argument("x", type=float)
@click.argument("y", type=float)
@click.option("--buffer", type=int, default=None, help="Radius in meters (0-500)")
@click.option("--hdb/--all", "hdb_only", default=None, help="HDB only?")
async def geocode_svy21(x: float, y: float, buffer: int | None, hdb_only: bool | None):
    """Reverse geocode from SVY21 X/Y."""
    from onemap_sg import reverse_geocode_svy21

    atype = "HDB" if hdb_only else ("All" if hdb_only is False else None)
    result = await reverse_geocode_svy21(x, y, buffer=buffer, address_type=atype)
    click.echo(json.dumps(result, indent=2, ensure_ascii=False))


# ===========================================================================
# route
# ===========================================================================


@main.group("route", cls=AsyncGroup)
def route():
    """Routing: walk, drive, cycle, transit."""


@route.command("walk", cls=AsyncCommand)
@click.argument("start")
@click.argument("end")
async def route_walk(start: str, end: str):
    """Walking route.  START/END: "lat,lon" or address/postal."""
    from onemap_sg import route_walk_drive_cycle

    s_lat, s_lon = await _resolve_location(start)
    e_lat, e_lon = await _resolve_location(end)
    result = await route_walk_drive_cycle(s_lat, s_lon, e_lat, e_lon, "walk")
    click.echo(json.dumps(result, indent=2, ensure_ascii=False))


@route.command("drive", cls=AsyncCommand)
@click.argument("start")
@click.argument("end")
async def route_drive(start: str, end: str):
    """Driving route.  START/END: "lat,lon" or address/postal."""
    from onemap_sg import route_walk_drive_cycle

    s_lat, s_lon = await _resolve_location(start)
    e_lat, e_lon = await _resolve_location(end)
    result = await route_walk_drive_cycle(s_lat, s_lon, e_lat, e_lon, "drive")
    click.echo(json.dumps(result, indent=2, ensure_ascii=False))


@route.command("cycle", cls=AsyncCommand)
@click.argument("start")
@click.argument("end")
async def route_cycle(start: str, end: str):
    """Cycling route.  START/END: "lat,lon" or address/postal."""
    from onemap_sg import route_walk_drive_cycle

    s_lat, s_lon = await _resolve_location(start)
    e_lat, e_lon = await _resolve_location(end)
    result = await route_walk_drive_cycle(s_lat, s_lon, e_lat, e_lon, "cycle")
    click.echo(json.dumps(result, indent=2, ensure_ascii=False))


@route.command("transit", cls=AsyncCommand)
@click.argument("start")
@click.argument("end")
@click.option("--time", "departure_time", default=None, help="RFC3339 or Unix timestamp: '09:00', '2026-06-08T09:00:00+08:00', or '1759381200' (default: now)")
@click.option("--mode", "transit_mode", default="TRANSIT", type=click.Choice(["TRANSIT", "BUS", "RAIL"]))
@click.option("--max-walk", type=int, default=None, help="Max walking distance (m)")
@click.option("--num", type=int, default=None, help="Number of itineraries (1-3)")
async def route_transit(start: str, end: str, departure_time: str | None, transit_mode: str, max_walk: int | None, num: int | None):
    """Public transport route.  START/END: "lat,lon" or address/postal."""
    from onemap_sg import route_public_transport

    if departure_time is None:
        departure_time = datetime.now().strftime("%Y-%m-%dT%H:%M:%S")

    s_lat, s_lon = await _resolve_location(start)
    e_lat, e_lon = await _resolve_location(end)
    result = await route_public_transport(
        s_lat, s_lon, e_lat, e_lon,
        departure_time=departure_time, mode=transit_mode,
        max_walk_distance=max_walk, num_itineraries=num,
    )
    click.echo(json.dumps(result, indent=2, ensure_ascii=False))


# ===========================================================================
# convert
# ===========================================================================


@main.group("convert", cls=AsyncGroup)
def convert():
    """Coordinate conversion between WGS84, SVY21, Web Mercator."""


_CONVERT_COMMANDS = [
    ("wgs84-to-svy21",    "convert_4326_to_3414", "latitude",  "longitude"),
    ("wgs84-to-mercator", "convert_4326_to_3857", "latitude",  "longitude"),
    ("svy21-to-wgs84",    "convert_3414_to_4326", "x",         "y"),
    ("svy21-to-mercator", "convert_3414_to_3857", "x",         "y"),
    ("mercator-to-svy21", "convert_3857_to_3414", "x",         "y"),
    ("mercator-to-wgs84", "convert_3857_to_4326", "x",         "y"),
]


def _make_convert_cmd(cmd_name: str, fn_name: str, a1: str, a2: str):
    @click.argument("b", type=float, metavar=a2.upper())
    @click.argument("a", type=float, metavar=a1.upper())
    async def cmd(a: float, b: float):
        from onemap_sg import coordinate

        fn = getattr(coordinate, fn_name)
        result = await fn(a, b)
        click.echo(json.dumps(result, indent=2, ensure_ascii=False))

    cmd.__name__ = cmd_name.replace("-", "_")
    return cmd


for _name, _fn, _a1, _a2 in _CONVERT_COMMANDS:
    c = _make_convert_cmd(_name, _fn, _a1, _a2)
    params = getattr(c, "__click_params__", None)
    convert.add_command(AsyncCommand(_name, callback=c, params=params))


# ===========================================================================
# theme
# ===========================================================================


@main.group("theme", cls=AsyncGroup)
def theme():
    """Thematic layers (amenities, boundaries, etc)."""


@theme.command("list", cls=AsyncCommand)
@click.option("--detail/--no-detail", default=False, help="Include full details")
async def theme_list(detail: bool):
    """List all available themes."""
    from onemap_sg import get_all_themes_info

    result = await get_all_themes_info(more_info="Y" if detail else "N")
    click.echo(json.dumps(result, indent=2, ensure_ascii=False))


@theme.command("info", cls=AsyncCommand)
@click.argument("query_name")
async def theme_info(query_name: str):
    """Get info about a specific theme."""
    from onemap_sg import get_theme_info

    result = await get_theme_info(query_name)
    click.echo(json.dumps(result, indent=2, ensure_ascii=False))


@theme.command("get", cls=AsyncCommand)
@click.argument("query_name")
@click.option("--extents", default=None, help="Bbox: lat1,lon1,lat2,lon2")
async def theme_get(query_name: str, extents: str | None):
    """Retrieve data for a theme."""
    from onemap_sg import retrieve_theme

    result = await retrieve_theme(query_name, extents=extents)
    click.echo(json.dumps(result, indent=2, ensure_ascii=False))


# ===========================================================================
# planning
# ===========================================================================


@main.group("planning", cls=AsyncGroup)
def planning():
    """Planning areas."""


@planning.command("all", cls=AsyncCommand)
@click.option("--year", type=int, default=None, help="Year (1998/2008/2014/2019)")
async def planning_all(year: int | None):
    """List all planning areas with polygons."""
    from onemap_sg import get_all_planning_areas

    result = await get_all_planning_areas(year=year)
    click.echo(json.dumps(result, indent=2, ensure_ascii=False))


@planning.command("names", cls=AsyncCommand)
@click.option("--year", type=int, default=None, help="Year (1998/2008/2014/2019)")
async def planning_names(year: int | None):
    """List planning area names."""
    from onemap_sg import get_planning_area_names

    result = await get_planning_area_names(year=year)
    click.echo(json.dumps(result, indent=2, ensure_ascii=False))


@planning.command("locate", cls=AsyncCommand)
@click.argument("latitude", type=float)
@click.argument("longitude", type=float)
@click.option("--year", type=int, default=None, help="Year (1998/2008/2014/2019)")
async def planning_locate(latitude: float, longitude: float, year: int | None):
    """Which planning area contains these coordinates?"""
    from onemap_sg import get_planning_area_by_location

    result = await get_planning_area_by_location(latitude, longitude, year=year)
    click.echo(json.dumps(result, indent=2, ensure_ascii=False))


# ===========================================================================
# population
# ===========================================================================


@main.group("pop", cls=AsyncGroup)
def pop():
    """Population & demographic queries."""


_POP_COMMANDS = {
    "age":              "get_population_age_group",
    "economic":         "get_economic_status",
    "education":        "get_education_status",
    "ethnic":           "get_ethnic_distribution",
    "income-hh":        "get_household_monthly_income",
    "size-hh":          "get_household_size",
    "structure-hh":     "get_household_structure",
    "income":           "get_income_from_work",
    "industry":         "get_industry_of_population",
    "language-lit":     "get_language_literacy",
    "marital":          "get_marital_status",
    "transport-school": "get_mode_of_transport_school",
    "transport-work":   "get_mode_of_transport_work",
    "religion":         "get_religion_data",
    "language-home":    "get_spoken_language_at_home",
    "tenancy":          "get_tenancy_data",
    "dwelling-hh":      "get_dwelling_type_household",
    "dwelling-pop":     "get_dwelling_type_population",
}


def _make_pop_cmd(fn_name: str):
    @click.argument("planning_area")
    @click.argument("year", type=int)
    @click.option("--gender", type=click.Choice(["male", "female"]), default=None)
    async def cmd(planning_area: str, year: int, gender: str | None):
        from onemap_sg import population

        fn = getattr(population, fn_name)
        try:
            if gender is not None:
                result = await fn(planning_area, year, gender=gender)
            else:
                result = await fn(planning_area, year)
        except TypeError:
            result = await fn(planning_area, year)
        click.echo(json.dumps(result, indent=2, ensure_ascii=False))

    return cmd


for _cmd_name, _fn_name in _POP_COMMANDS.items():
    c = _make_pop_cmd(_fn_name)
    c.__name__ = _cmd_name.replace("-", "_")
    params = getattr(c, "__click_params__", None)
    pop.add_command(AsyncCommand(
        _cmd_name, callback=c, params=params,
        help=f"{_cmd_name} distribution",
    ))


# ===========================================================================
# nearby transport
# ===========================================================================


@main.group("nearby", cls=AsyncGroup)
def nearby():
    """Nearby transport: MRT stations, bus stops."""


@nearby.command("mrt", cls=AsyncCommand)
@click.argument("latitude", type=float)
@click.argument("longitude", type=float)
@click.option("--radius", type=int, default=None, help="Radius in meters (1-5000)")
async def nearby_mrt(latitude: float, longitude: float, radius: int | None):
    """Find nearby MRT/LRT stations."""
    from onemap_sg import get_nearby_mrt_stations

    result = await get_nearby_mrt_stations(latitude, longitude, radius_in_meters=radius)
    click.echo(json.dumps(result, indent=2, ensure_ascii=False))


@nearby.command("bus", cls=AsyncCommand)
@click.argument("latitude", type=float)
@click.argument("longitude", type=float)
@click.option("--radius", type=int, default=None, help="Radius in meters (1-5000)")
async def nearby_bus(latitude: float, longitude: float, radius: int | None):
    """Find nearby bus stops."""
    from onemap_sg import get_nearby_bus_stops

    result = await get_nearby_bus_stops(latitude, longitude, radius_in_meters=radius)
    click.echo(json.dumps(result, indent=2, ensure_ascii=False))


# ===========================================================================
# amenities
# ===========================================================================


@main.group("amenity", cls=AsyncGroup)
def amenity():
    """Nearby amenities."""


@amenity.command("nearby", cls=AsyncCommand)
@click.argument("latitude", type=float)
@click.argument("longitude", type=float)
@click.argument("type_", metavar="TYPE")
@click.option("--radius", type=float, default=1000, help="Radius in meters")
async def amenity_nearby(latitude: float, longitude: float, type_: str, radius: float):
    """Find amenities near a location.

    TYPE: hawker_centres, kindergartens, childcare, community_clubs, parks,
    nparks, hospitals, polyclinics, libraries, sports_facilities,
    eldercare, heritage_trees, monuments, hotels"""
    from onemap_sg import get_nearby_amenities

    result = await get_nearby_amenities(latitude, longitude, type_, radius_meters=radius)
    click.echo(json.dumps(result, indent=2, ensure_ascii=False))


# ===========================================================================
# map
# ===========================================================================


@main.command("map", cls=AsyncCommand)
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
async def map_cmd(layer: str, lat: float | None, lon: float | None, postal: str | None,
                  zoom: int, width: int, height: int, points: str | None,
                  lines: str | None, polygons: str | None, color: str | None,
                  fill_color: str | None, output: str | None):
    """Generate static map image (returns base64 PNG)."""
    from onemap_sg import get_static_map

    result = await get_static_map(
        layer_chosen=layer,
        zoom=zoom, width=width, height=height,
        latitude=lat, longitude=lon, postal=postal,
        points=points, lines=lines, polygons=polygons,
        color=color, fill_color=fill_color,
    )

    if output and result.get("image_base64"):
        import base64
        with open(output, "wb") as f:
            f.write(base64.b64decode(result["image_base64"]))
        click.echo(f"Saved {output}")
    else:
        summary = {k: v for k, v in result.items() if k != "image_base64"}
        click.echo(json.dumps(summary, indent=2))


# ===========================================================================
# elevation
# ===========================================================================


@main.group("elevation", cls=AsyncGroup)
def elevation():
    """Terrain elevation."""


@elevation.command("point", cls=AsyncCommand)
@click.argument("latitude", type=float)
@click.argument("longitude", type=float)
async def elevation_point(latitude: float, longitude: float):
    """Get elevation at a point."""
    from onemap_sg import get_elevation

    result = await get_elevation(latitude, longitude)
    click.echo(json.dumps(result, indent=2, ensure_ascii=False))


@elevation.command("profile", cls=AsyncCommand)
@click.argument("coordinates")
async def elevation_profile(coordinates: str):
    """Get elevation profile: "lat1,lon1|lat2,lon2|..." """
    from onemap_sg import get_elevation_profile

    result = await get_elevation_profile(coordinates)
    click.echo(json.dumps(result, indent=2, ensure_ascii=False))


# ===========================================================================
# ura
# ===========================================================================


@main.group("ura", cls=AsyncGroup)
def ura():
    """URA property & planning data."""


@ura.command("transactions", cls=AsyncCommand)
@click.option("--batch", type=int, default=1, help="Batch 1-4 by district")
async def ura_transactions(batch: int):
    """Private residential sales transactions (5yr)."""
    from onemap_sg.ura import get_private_residential_transactions

    result = await get_private_residential_transactions(batch)
    click.echo(json.dumps(result, indent=2, ensure_ascii=False))


@ura.command("rentals", cls=AsyncCommand)
@click.option("--period", default="25q4", help="Quarter in yyqq format")
async def ura_rentals(period: str):
    """Private residential rental contracts."""
    from onemap_sg.ura import get_private_rental_contracts

    result = await get_private_rental_contracts(period)
    click.echo(json.dumps(result, indent=2, ensure_ascii=False))


@ura.command("median-rentals", cls=AsyncCommand)
async def ura_median():
    """Median rentals (past 3 years)."""
    from onemap_sg.ura import get_median_rentals

    result = await get_median_rentals()
    click.echo(json.dumps(result, indent=2, ensure_ascii=False))


@ura.command("developer-sales", cls=AsyncCommand)
@click.option("--period", default="0925", help="Month in mmyy format")
async def ura_dev_sales(period: str):
    """Developer sales (past 3 years)."""
    from onemap_sg.ura import get_developer_sales

    result = await get_developer_sales(period)
    click.echo(json.dumps(result, indent=2, ensure_ascii=False))


@ura.command("pipeline", cls=AsyncCommand)
async def ura_pipeline():
    """Upcoming residential projects."""
    from onemap_sg.ura import get_residential_pipeline

    result = await get_residential_pipeline()
    click.echo(json.dumps(result, indent=2, ensure_ascii=False))


@ura.command("decisions", cls=AsyncCommand)
@click.option("--year", type=int, default=2025, help="Year (after 2000)")
async def ura_decisions(year: int):
    """Planning decisions."""
    from onemap_sg.ura import get_planning_decisions

    result = await get_planning_decisions(year)
    click.echo(json.dumps(result, indent=2, ensure_ascii=False))


@ura.command("carpark-avail", cls=AsyncCommand)
async def ura_carpark_avail():
    """Real-time car park availability."""
    from onemap_sg.ura import get_car_park_availability

    result = await get_car_park_availability()
    click.echo(json.dumps(result, indent=2, ensure_ascii=False))


@ura.command("carpark-details", cls=AsyncCommand)
async def ura_carpark_details():
    """Car park list and rates."""
    from onemap_sg.ura import get_car_park_details

    result = await get_car_park_details()
    click.echo(json.dumps(result, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
