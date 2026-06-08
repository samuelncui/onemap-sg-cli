"""
OneMap static map API — generate static map images with optional overlays.

Returns a base64-encoded PNG image with configurable basemap style, zoom,
dimensions, and optional point/polygon/line overlays.
"""

from __future__ import annotations

import base64
from typing import Any

from onemap_sg._client import (
    BASE_URL,
    REQUEST_TIMEOUT,
    STATIC_MAP_ENDPOINT,
    _get_async_client,
)


async def get_static_map(
    layer_chosen: str,
    zoom: int,
    width: int,
    height: int,
    latitude: float | None = None,
    longitude: float | None = None,
    postal: str | None = None,
    polygons: str | None = None,
    lines: str | None = None,
    points: str | None = None,
    color: str | None = None,
    fill_color: str | None = None,
) -> dict[str, Any]:
    """Generate a static map image in PNG format with optional overlays.

    Returns the image as base64-encoded PNG data. Users can overlay points,
    polygons, or polylines on the map.

    API Reference: https://www.onemap.gov.sg/apidocs/staticmap

    Args:
        layer_chosen: Base map style - "night", "grey", "original",
            "default", or "landlot". Required.
        zoom: Zoom level (11-19). Lower values = more zoomed out. Required.
        width: Image width in pixels (128-512). Required.
        height: Image height in pixels (128-512). Required.
        latitude: Latitude in WGS84 format. Either lat/lon or postal required.
        longitude: Longitude in WGS84 format. Either lat/lon or postal
            required.
        postal: Postal code. Either lat/lon or postal required.
        polygons: Polygon coordinates to overlay. Format:
            "[[lat1,lon1],[lat2,lon2],...,[lat1,lon1]]:R,G,B"
            Multiple polygons separated by pipe (|).
        lines: Line coordinates to overlay. Format:
            "[[lat1,lon1],[lat2,lon2]]:R,G,B:thickness"
            Multiple lines separated by pipe (|).
        points: Point coordinates to overlay. Format:
            "[lat,lon,\"R,G,B\"]|[lat,lon,\"R,G,B\"]"
        color: Color for all lines in RGB format (e.g., "255,0,255").
        fill_color: Fill color for all polygons in RGB format (e.g.,
            "0,255,0").

    Returns:
        JSON dict with base64-encoded PNG image data and metadata.

    Raises:
        ValueError: If any parameter validation fails.
    """
    from onemap_sg._client import _token_manager as tm

    valid_layers = ["night", "grey", "original", "default", "landlot"]
    if layer_chosen not in valid_layers:
        raise ValueError(
            f"Invalid layer_chosen. Must be one of: {', '.join(valid_layers)}"
        )

    if zoom < 11 or zoom > 19:
        raise ValueError("Please enter a valid zoom level (11-19).")

    if width < 128 or width > 512:
        raise ValueError("Please enter a valid width (128-512 pixels).")

    if height < 128 or height > 512:
        raise ValueError("Please enter a valid height (128-512 pixels).")

    has_coordinates = latitude is not None and longitude is not None
    has_postal = postal is not None and postal.strip() != ""
    if not has_coordinates and not has_postal:
        raise ValueError(
            "Please enter a pair of valid latitude & longitude, "
            "or a postal code."
        )

    params: dict[str, Any] = {
        "layerchosen": layer_chosen,
        "zoom": zoom,
        "width": width,
        "height": height,
    }

    if latitude is not None:
        params["latitude"] = latitude
    if longitude is not None:
        params["longitude"] = longitude
    if postal is not None:
        params["postal"] = postal
    if polygons is not None:
        params["polygons"] = polygons
    if lines is not None:
        params["lines"] = lines
    if points is not None:
        params["points"] = points
    if color is not None:
        params["color"] = color
    if fill_color is not None:
        params["fillColor"] = fill_color

    access_token = await tm.get_access_token()
    client = await _get_async_client(BASE_URL, REQUEST_TIMEOUT)

    response = await client.get(
        STATIC_MAP_ENDPOINT,
        params=params,
        headers={"Authorization": access_token},
    )
    response.raise_for_status()

    image_base64 = base64.b64encode(response.content).decode("utf-8")

    return {
        "image_base64": image_base64,
        "content_type": response.headers.get("content-type", "image/png"),
        "size_bytes": len(response.content),
        "width": width,
        "height": height,
    }
