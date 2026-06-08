"""
OneMap elevation API — terrain elevation from coordinates.

Uses the Open-Elevation API (global SRTM 30m resolution data) to get
terrain height above sea level for single points or along a path profile.
"""

from __future__ import annotations

from typing import Any

from onemap_sg._client import (
    ELEVATION_API_URL,
    REQUEST_TIMEOUT,
    _get_async_client,
)


async def get_elevation(latitude: float, longitude: float) -> dict[str, Any]:
    """Get terrain elevation at a specific coordinate.

    Uses the Open-Elevation API to get terrain height above sea level.
    This is useful for 3D mapping and terrain analysis in Singapore.

    Note: This uses global SRTM data (30m resolution). For higher precision
    Singapore-specific elevation data, consider SLA GeoSpace (requires
    subscription).

    Args:
        latitude: Latitude in WGS84 (e.g., 1.3521).
        longitude: Longitude in WGS84 (e.g., 103.8198).

    Returns:
        JSON dict with elevation in meters above sea level.

    Raises:
        httpx.HTTPError: If the elevation service request fails.
    """
    client = await _get_async_client(ELEVATION_API_URL, REQUEST_TIMEOUT)

    response = await client.get(
        "", params={"locations": f"{latitude},{longitude}"}
    )
    response.raise_for_status()

    data = response.json()

    if "results" in data and len(data["results"]) > 0:
        elevation = data["results"][0].get("elevation")
        return {
            "latitude": latitude,
            "longitude": longitude,
            "elevation_meters": elevation,
            "data_source": "Open-Elevation (SRTM 30m)",
        }

    raise ValueError("No elevation data available for this location.")


async def get_elevation_profile(coordinates: str) -> dict[str, Any]:
    """Get elevation profile for multiple points along a path.

    Useful for analyzing terrain along a route or transect.

    Args:
        coordinates: Pipe-separated lat,lon pairs
            (e.g., "1.35,103.82|1.36,103.83|1.37,103.84").

    Returns:
        JSON dict with elevation for each point and summary statistics.

    Raises:
        ValueError: If coordinate format is invalid or point count is wrong.
    """
    # Parse coordinates
    points = []
    for pair in coordinates.split("|"):
        try:
            lat, lon = pair.strip().split(",")
            points.append({"latitude": float(lat), "longitude": float(lon)})
        except ValueError as exc:
            raise ValueError(f"Invalid coordinates format: {exc}") from exc

    if len(points) < 2:
        raise ValueError(
            "At least 2 coordinate pairs required for elevation profile."
        )

    if len(points) > 100:
        raise ValueError("Maximum 100 points allowed per request.")

    # Build request for Open-Elevation API
    locations = "|".join(
        [f"{p['latitude']},{p['longitude']}" for p in points]
    )

    client = await _get_async_client(ELEVATION_API_URL, REQUEST_TIMEOUT)

    response = await client.get(
        "", params={"locations": locations}
    )
    response.raise_for_status()

    data = response.json()

    if "results" in data:
        profile = []
        for i, result in enumerate(data["results"]):
            profile.append({
                "point_index": i,
                "latitude": result.get("latitude"),
                "longitude": result.get("longitude"),
                "elevation_meters": result.get("elevation"),
            })

        elevations = [
            p["elevation_meters"]
            for p in profile
            if p["elevation_meters"] is not None
        ]

        return {
            "profile": profile,
            "statistics": {
                "min_elevation": min(elevations) if elevations else None,
                "max_elevation": max(elevations) if elevations else None,
                "elevation_range": (
                    max(elevations) - min(elevations)
                    if elevations
                    else None
                ),
                "point_count": len(profile),
            },
            "data_source": "Open-Elevation (SRTM 30m)",
        }

    raise ValueError("No elevation data available.")
