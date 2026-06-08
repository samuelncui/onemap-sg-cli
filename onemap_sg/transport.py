"""
OneMap nearby transport API — find MRT/LRT stations and bus stops by location.

Provides functions to query nearby public transport infrastructure including
MRT/LRT stations and bus stops within a specified search radius.
"""

from __future__ import annotations

from typing import Any

from onemap_sg._client import _call_api, NEARBY_BUS, NEARBY_MRT


async def get_nearby_mrt_stations(
    latitude: float,
    longitude: float,
    radius_in_meters: int | None = None,
) -> dict[str, Any]:
    """Find nearby MRT and LRT stations from a given location.

    API Reference: https://www.onemap.gov.sg/apidocs/nearbytransport

    Args:
        latitude: Latitude in WGS84 format. Required.
        longitude: Longitude in WGS84 format. Required.
        radius_in_meters: Search radius (default 2000, max 5000). Must be
            between 1 and 5000.

    Returns:
        JSON dict list of nearby stations with id, name, coordinates, and road.

    Raises:
        ValueError: If radius_in_meters is outside the range 1-5000.
    """
    if radius_in_meters is not None and (
        radius_in_meters < 1 or radius_in_meters > 5000
    ):
        raise ValueError("radius_in_meters must be between 1 and 5000.")

    params: dict[str, Any] = {"latitude": latitude, "longitude": longitude}
    if radius_in_meters is not None:
        params["radius_in_meters"] = radius_in_meters
    return await _call_api(NEARBY_MRT, params)


async def get_nearby_bus_stops(
    latitude: float,
    longitude: float,
    radius_in_meters: int | None = None,
) -> dict[str, Any]:
    """Find nearby bus stops from a given location.

    API Reference: https://www.onemap.gov.sg/apidocs/nearbytransport

    Args:
        latitude: Latitude in WGS84 format. Required.
        longitude: Longitude in WGS84 format. Required.
        radius_in_meters: Search radius (default 2000, max 5000). Must be
            between 1 and 5000.

    Returns:
        JSON dict list of nearby bus stops with id, name, coordinates, and
        road.

    Raises:
        ValueError: If radius_in_meters is outside the range 1-5000.
    """
    if radius_in_meters is not None and (
        radius_in_meters < 1 or radius_in_meters > 5000
    ):
        raise ValueError("radius_in_meters must be between 1 and 5000.")

    params: dict[str, Any] = {"latitude": latitude, "longitude": longitude}
    if radius_in_meters is not None:
        params["radius_in_meters"] = radius_in_meters
    return await _call_api(NEARBY_BUS, params)
