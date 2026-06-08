"""
OneMap planning area API — Singapore planning area boundaries and lookup.

Singapore has 55 planning areas delineated by the Urban Redevelopment Authority.
This module provides access to planning area polygons, names, and location-based
lookup by year.
"""

from __future__ import annotations

from typing import Any

from onemap_sg._client import (
    _call_api,
    PLANNING_AREA_ALL,
    PLANNING_AREA_NAMES,
    PLANNING_AREA_QUERY,
)

VALID_PLANNING_YEARS = [1998, 2008, 2014, 2019]


async def get_all_planning_areas(year: int | None = None) -> dict[str, Any]:
    """Get all planning area polygons in Singapore.

    Singapore has 55 planning areas delineated by the Urban Redevelopment
    Authority.

    API Reference: https://www.onemap.gov.sg/apidocs/planningarea

    Args:
        year: Optional year (1998, 2008, 2014, 2019). Defaults to latest.

    Returns:
        JSON dict with planning area names and GeoJSON polygon geometries.

    Raises:
        ValueError: If year is provided but not one of the valid years.
    """
    if year is not None and year not in VALID_PLANNING_YEARS:
        raise ValueError(
            f"Please enter valid year. Valid years are: {VALID_PLANNING_YEARS}"
        )

    params: dict[str, Any] = {"year": year} if year else {}
    return await _call_api(PLANNING_AREA_ALL, params)


async def get_planning_area_names(year: int | None = None) -> dict[str, Any]:
    """Get names of all planning areas in Singapore.

    API Reference: https://www.onemap.gov.sg/apidocs/planningarea

    Args:
        year: Optional year (1998, 2008, 2014, 2019). Defaults to latest.

    Returns:
        JSON dict list of planning area names and IDs.

    Raises:
        ValueError: If year is provided but not one of the valid years.
    """
    if year is not None and year not in VALID_PLANNING_YEARS:
        raise ValueError(
            f"Please enter valid year. Valid years are: {VALID_PLANNING_YEARS}"
        )

    params: dict[str, Any] = {"year": year} if year else {}
    return await _call_api(PLANNING_AREA_NAMES, params)


async def get_planning_area_by_location(
    latitude: float,
    longitude: float,
    year: int | None = None,
) -> dict[str, Any]:
    """Get the planning area for a specific location.

    API Reference: https://www.onemap.gov.sg/apidocs/planningarea

    Args:
        latitude: Latitude in WGS84 format.
        longitude: Longitude in WGS84 format.
        year: Optional year (1998, 2008, 2014, 2019). Defaults to latest.

    Returns:
        JSON dict with planning area name and GeoJSON polygon geometry.

    Raises:
        ValueError: If year is provided but not one of the valid years.
    """
    if year is not None and year not in VALID_PLANNING_YEARS:
        raise ValueError(
            f"Please enter valid year. Valid years are: {VALID_PLANNING_YEARS}"
        )

    params: dict[str, Any] = {"latitude": latitude, "longitude": longitude}
    if year:
        params["year"] = year
    return await _call_api(PLANNING_AREA_QUERY, params)
