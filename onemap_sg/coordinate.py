"""
OneMap coordinate converter APIs — EPSG coordinate system transformations.

Supports conversion between three coordinate reference systems:
- EPSG:4326 — WGS84 (latitude/longitude)
- EPSG:3414 — SVY21 (Singapore projected X/Y)
- EPSG:3857 — Web Mercator
"""

from __future__ import annotations

from typing import Any

from onemap_sg._client import (
    _call_api,
    CONVERT_4326_TO_3857,
    CONVERT_4326_TO_3414,
    CONVERT_3414_TO_3857,
    CONVERT_3414_TO_4326,
    CONVERT_3857_TO_3414,
    CONVERT_3857_TO_4326,
)


async def convert_4326_to_3857(
    latitude: float, longitude: float
) -> dict[str, Any]:
    """Convert coordinates from EPSG:4326 (WGS84) to EPSG:3857 (Web Mercator).

    API Reference: https://www.onemap.gov.sg/apidocs/coordinate

    Args:
        latitude: Latitude in WGS84 format.
        longitude: Longitude in WGS84 format.

    Returns:
        JSON dict with X and Y coordinates in EPSG:3857 format.
    """
    return await _call_api(
        CONVERT_4326_TO_3857, {"latitude": latitude, "longitude": longitude}
    )


async def convert_4326_to_3414(
    latitude: float, longitude: float
) -> dict[str, Any]:
    """Convert coordinates from EPSG:4326 (WGS84) to EPSG:3414 (SVY21).

    API Reference: https://www.onemap.gov.sg/apidocs/coordinate

    Args:
        latitude: Latitude in WGS84 format.
        longitude: Longitude in WGS84 format.

    Returns:
        JSON dict with X and Y coordinates in SVY21 format.
    """
    return await _call_api(
        CONVERT_4326_TO_3414, {"latitude": latitude, "longitude": longitude}
    )


async def convert_3414_to_3857(x: float, y: float) -> dict[str, Any]:
    """Convert coordinates from EPSG:3414 (SVY21) to EPSG:3857 (Web Mercator).

    API Reference: https://www.onemap.gov.sg/apidocs/coordinate

    Args:
        x: X coordinate in SVY21 format.
        y: Y coordinate in SVY21 format.

    Returns:
        JSON dict with X and Y coordinates in EPSG:3857 format.
    """
    return await _call_api(CONVERT_3414_TO_3857, {"X": x, "Y": y})


async def convert_3414_to_4326(x: float, y: float) -> dict[str, Any]:
    """Convert coordinates from EPSG:3414 (SVY21) to EPSG:4326 (WGS84).

    API Reference: https://www.onemap.gov.sg/apidocs/coordinate

    Args:
        x: X coordinate in SVY21 format.
        y: Y coordinate in SVY21 format.

    Returns:
        JSON dict with latitude and longitude in WGS84 format.
    """
    return await _call_api(CONVERT_3414_TO_4326, {"X": x, "Y": y})


async def convert_3857_to_3414(x: float, y: float) -> dict[str, Any]:
    """Convert coordinates from EPSG:3857 (Web Mercator) to EPSG:3414 (SVY21).

    API Reference: https://www.onemap.gov.sg/apidocs/coordinate

    Args:
        x: X coordinate in EPSG:3857 format.
        y: Y coordinate in EPSG:3857 format.

    Returns:
        JSON dict with X and Y coordinates in SVY21 format.
    """
    return await _call_api(CONVERT_3857_TO_3414, {"X": x, "Y": y})


async def convert_3857_to_4326(x: float, y: float) -> dict[str, Any]:
    """Convert coordinates from EPSG:3857 (Web Mercator) to EPSG:4326 (WGS84).

    API Reference: https://www.onemap.gov.sg/apidocs/coordinate

    Args:
        x: X coordinate in EPSG:3857 format.
        y: Y coordinate in EPSG:3857 format.

    Returns:
        JSON dict with latitude and longitude in WGS84 format.
    """
    return await _call_api(CONVERT_3857_TO_4326, {"X": x, "Y": y})
