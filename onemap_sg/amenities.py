"""
OneMap amenities API — find nearby amenities by location.

A convenience module that queries OneMap themes to find amenities
within a bounding box around a specified location, with calculated
distance information for each result.
"""

from __future__ import annotations

import math
from typing import Any

from onemap_sg._client import _call_api, THEME_RETRIEVE

# Mapping from friendly amenity type names to OneMap theme query names
AMENITY_THEMES: dict[str, str] = {
    "hawker_centres": "ssot_hawkercentres",
    "kindergartens": "kindergartens",
    "childcare": "childcare",
    "community_clubs": "communityclubs",
    "parks": "nationalparks",
    "nparks": "nparks_parks",
    "hospitals": "moh_hospitals",
    "polyclinics": "vaccination_polyclinics",
    "libraries": "libraries",
    "sports_facilities": "sportsg_sport_facilities",
    "eldercare": "eldercare",
    "heritage_trees": "heritagetrees",
    "monuments": "monuments",
    "hotels": "hotels",
}


async def get_nearby_amenities(
    latitude: float,
    longitude: float,
    amenity_type: str,
    radius_meters: float = 1000,
) -> dict[str, Any]:
    """Get amenities near a location within a specified radius.

    This is a convenience function that queries OneMap themes for amenities
    within a bounding box around the specified location.

    Args:
        latitude: Center point latitude (WGS84).
        longitude: Center point longitude (WGS84).
        amenity_type: Type of amenity. Options: hawker_centres, kindergartens,
            childcare, community_clubs, parks, nparks, hospitals,
            polyclinics, libraries, sports_facilities, eldercare,
            heritage_trees, monuments, hotels.
        radius_meters: Search radius in meters (default 1000m).

    Returns:
        JSON dict with amenities found, including names, descriptions, and
        coordinates, with distance_meters added to each result.

    Raises:
        ValueError: If amenity_type is not valid.
    """
    if amenity_type not in AMENITY_THEMES:
        raise ValueError(
            f"Invalid amenity_type. Valid options: "
            f"{list(AMENITY_THEMES.keys())}"
        )

    # Approximate degrees per meter at Singapore's latitude (~1.3°N)
    lat_delta = radius_meters / 111000
    lon_delta = radius_meters / 110900

    extents = (
        f"{latitude - lat_delta},{longitude - lon_delta},"
        f"{latitude + lat_delta},{longitude + lon_delta}"
    )
    query_name = AMENITY_THEMES[amenity_type]

    result = await _call_api(
        THEME_RETRIEVE, {"queryName": query_name, "extents": extents}
    )

    # Add distance information to each result
    if "SrchResults" in result and len(result["SrchResults"]) > 1:
        for item in result["SrchResults"][1:]:  # Skip first item (metadata)
            if "LatLng" in item:
                try:
                    coords = item["LatLng"]
                    if isinstance(coords, str):
                        if coords.startswith("[["):
                            # Polygon format — skip
                            continue
                        # Point format "lon,lat" or similar
                        parts = (
                            coords.replace("[", "")
                            .replace("]", "")
                            .split(",")
                        )
                        if len(parts) >= 2:
                            item_lon = float(parts[0])
                            item_lat = float(parts[1])
                            # Haversine distance
                            R = 6371000  # Earth radius in meters
                            dlat = math.radians(item_lat - latitude)
                            dlon = math.radians(item_lon - longitude)
                            a = (
                                math.sin(dlat / 2) ** 2
                                + math.cos(math.radians(latitude))
                                * math.cos(math.radians(item_lat))
                                * math.sin(dlon / 2) ** 2
                            )
                            c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
                            item["distance_meters"] = round(R * c)
                except (ValueError, TypeError, IndexError):
                    pass

    return result
