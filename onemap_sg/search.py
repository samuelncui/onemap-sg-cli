"""
OneMap search API — address and location search.

Provides search functionality for buildings, roads, postal codes,
bus stop numbers, and other location data.
"""

from __future__ import annotations

import re
from typing import Any

from onemap_sg._client import _call_api, SEARCH_ENDPOINT


async def search(
    search_value: str,
    return_geometry: str = "Y",
    get_address_details: str = "Y",
    page_number: int | None = None,
) -> dict[str, Any]:
    """Search for address information for roads, buildings, postal codes, etc.

    This API takes a text input (building name, road name, bus stop number, or
    postal code) and returns address information including coordinates.

    API Reference: https://www.onemap.gov.sg/apidocs/search

    Args:
        search_value: Keywords to search (e.g., "Revenue House", "307987",
            "Orchard Road"). Cannot be empty.
        return_geometry: "Y" to return geometry/coordinates, "N" otherwise.
        get_address_details: "Y" to return detailed address info, "N" otherwise.
        page_number: Optional page number for paginated results (must be
            positive integer).

    Returns:
        JSON dict with search results including address, coordinates,
        postal code, etc.

    Raises:
        ValueError: If any parameter validation fails.
    """
    # Validate search_value is not empty
    if not search_value or not search_value.strip():
        raise ValueError("Parameter searchVal is invalid. Cannot be empty.")

    # Validate return_geometry
    if return_geometry not in ("Y", "N"):
        raise ValueError("Invalid return_geometry value. Must be 'Y' or 'N'.")

    # Validate get_address_details
    if get_address_details not in ("Y", "N"):
        raise ValueError("Invalid get_address_details value. Must be 'Y' or 'N'.")

    # Validate page_number if provided
    if page_number is not None and page_number < 1:
        raise ValueError(
            "Please state a valid page number. Must be a positive integer."
        )

    params: dict[str, Any] = {
        "searchVal": search_value,
        "returnGeom": return_geometry,
        "getAddrDetails": get_address_details,
    }
    if page_number is not None:
        params["pageNum"] = page_number

    return await _call_api(SEARCH_ENDPOINT, params)
