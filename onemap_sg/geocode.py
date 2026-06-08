"""
OneMap reverse geocode APIs — coordinate-to-address conversion.

Supports both WGS84 (lat/lon) and SVY21 (X/Y) coordinate systems
for reverse geocoding to Singapore addresses.
"""

from __future__ import annotations

from typing import Any

from onemap_sg._client import (
    _call_api,
    REVGEOCODE_WGS84_ENDPOINT,
    REVGEOCODE_SVY21_ENDPOINT,
)


async def reverse_geocode_wgs84(
    latitude: float,
    longitude: float,
    buffer: int | None = None,
    address_type: str | None = None,
) -> dict[str, Any]:
    """Get address information for a location using WGS84 coordinates (lat/lon).

    Returns addresses within a specified buffer/radius of the location.
    Maximum buffer is 500m for buildings and 20m for roads.

    API Reference: https://www.onemap.gov.sg/apidocs/reverseGeocode

    Args:
        latitude: Latitude in WGS84 format (e.g., 1.3254295).
        longitude: Longitude in WGS84 format (e.g., 103.9005321).
        buffer: Optional radius in meters (0-500). Default searches nearby.
        address_type: "HDB" for HDB properties only, "All" for all property types.

    Returns:
        JSON dict with geocoded address information including building name,
        road, postal code.

    Raises:
        ValueError: If buffer or address_type validation fails.
    """
    # Validate buffer range
    if buffer is not None and (buffer < 0 or buffer > 500):
        raise ValueError("Buffer must be between 0 and 500 meters.")

    # Validate address_type
    if address_type is not None and address_type not in ("HDB", "All"):
        raise ValueError("Invalid address_type. Must be 'HDB' or 'All'.")

    params: dict[str, Any] = {"location": f"{latitude},{longitude}"}
    if buffer is not None:
        params["buffer"] = buffer
    if address_type is not None:
        params["addressType"] = address_type

    return await _call_api(REVGEOCODE_WGS84_ENDPOINT, params)


async def reverse_geocode_svy21(
    x: float,
    y: float,
    buffer: int | None = None,
    address_type: str | None = None,
) -> dict[str, Any]:
    """Get address information for a location using SVY21 coordinates (X/Y).

    Returns addresses within a specified buffer/radius of the location.
    Maximum buffer is 500m for buildings and 20m for roads.

    API Reference: https://www.onemap.gov.sg/apidocs/reverseGeocode

    Args:
        x: X coordinate in SVY21 format (e.g., 24291.97788882387).
        y: Y coordinate in SVY21 format (e.g., 31373.0117224489).
        buffer: Optional radius in meters (0-500). Default searches nearby.
        address_type: "HDB" for HDB properties only, "All" for all property types.

    Returns:
        JSON dict with geocoded address information including building name,
        road, postal code.

    Raises:
        ValueError: If buffer or address_type validation fails.
    """
    # Validate buffer range
    if buffer is not None and (buffer < 0 or buffer > 500):
        raise ValueError("Buffer must be between 0 and 500 meters.")

    # Validate address_type
    if address_type is not None and address_type not in ("HDB", "All"):
        raise ValueError("Invalid address_type. Must be 'HDB' or 'All'.")

    params: dict[str, Any] = {"location": f"{x},{y}"}
    if buffer is not None:
        params["buffer"] = buffer
    if address_type is not None:
        params["addressType"] = address_type

    return await _call_api(REVGEOCODE_SVY21_ENDPOINT, params)
