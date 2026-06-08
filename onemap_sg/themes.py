"""
OneMap themes API — access thematic layers for locations, amenities, boundaries.

Provides functions to query OneMap thematic layers from various government
agencies, including amenity locations, boundary data, and facility information.
"""

from __future__ import annotations

from typing import Any

from onemap_sg._client import (
    _call_api,
    THEME_CHECK_STATUS,
    THEME_GET_ALL_INFO,
    THEME_GET_INFO,
    THEME_RETRIEVE,
)


async def get_all_themes_info(more_info: str = "N") -> dict[str, Any]:
    """Get a list of all available thematic layers in OneMap.

    OneMap has over 100 thematic layers provided by various government agencies,
    including locations for amenities, boundaries, facilities, etc.

    API Reference: https://www.onemap.gov.sg/apidocs/themes

    Args:
        more_info: "Y" to include icon names, category names, and theme owners.

    Returns:
        JSON dict with list of themes including THEMENAME and QUERYNAME.

    Raises:
        ValueError: If more_info is not "Y" or "N".
    """
    if more_info not in ("Y", "N"):
        raise ValueError("Invalid more_info value. Must be 'Y' or 'N'.")

    return await _call_api(THEME_GET_ALL_INFO, {"moreInfo": more_info})


async def get_theme_info(query_name: str) -> dict[str, Any]:
    """Get information about a specific theme by its query name.

    API Reference: https://www.onemap.gov.sg/apidocs/themes

    Args:
        query_name: The theme's query name (e.g., "kindergartens",
            "communityclubs"). Required.

    Returns:
        JSON dict with theme details including THEMENAME and QUERYNAME.

    Raises:
        ValueError: If query_name is empty.
    """
    if not query_name or not query_name.strip():
        raise ValueError("There is no query name.")

    return await _call_api(THEME_GET_INFO, {"queryName": query_name})


async def check_theme_status(query_name: str, date_time: str) -> dict[str, Any]:
    """Check if a theme has been updated since a specific datetime.

    API Reference: https://www.onemap.gov.sg/apidocs/themes

    Args:
        query_name: The theme's query name (e.g., "kindergartens"). Required.
        date_time: DateTime in ISO format (e.g., "2023-06-15T16:00:00.000Z").
            Required.

    Returns:
        JSON dict with UpdatedFile boolean indicating if theme was updated.

    Raises:
        ValueError: If query_name or date_time is empty.
    """
    if not query_name or not query_name.strip():
        raise ValueError("There is no query name.")

    if not date_time or not date_time.strip():
        raise ValueError("Your date provided is empty.")

    return await _call_api(
        THEME_CHECK_STATUS, {"queryName": query_name, "dateTime": date_time}
    )


async def retrieve_theme(
    query_name: str, extents: str | None = None
) -> dict[str, Any]:
    """Retrieve all data for a specific theme, optionally within a bounding box.

    API Reference: https://www.onemap.gov.sg/apidocs/themes

    Args:
        query_name: The theme's query name (e.g., "dengue_cluster",
            "kindergartens"). Required.
        extents: Optional bounding box as "lat1,lon1,lat2,lon2"
            (e.g., "1.291789,103.7796402,1.3290461,103.8726032").

    Returns:
        JSON dict with theme data including locations, descriptions, and
        GeoJSON geometries.

    Raises:
        ValueError: If query_name is empty.
    """
    if not query_name or not query_name.strip():
        raise ValueError("There is no query name.")

    params: dict[str, Any] = {"queryName": query_name}
    if extents is not None:
        params["extents"] = extents
    return await _call_api(THEME_RETRIEVE, params)
