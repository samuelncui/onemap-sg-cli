"""
OneMap routing APIs — walk, drive, cycle, and public transport routes.

Provides route calculation between two points for multiple transport modes
including public transit with itinerary planning.
"""

from __future__ import annotations

import re
from datetime import datetime
from typing import Any

from onemap_sg._client import _call_api, ROUTING_ENDPOINT


# RFC 3339 datetime: "2026-06-08T15:35:00+08:00" or "15:35:00"
# Unix timestamp (seconds): "1759381200"
_RFC3339_RE = re.compile(
    r"^"
    r"(?:(\d{4}-\d{2}-\d{2})T)?"         # optional date YYYY-MM-DD
    r"(\d{1,2}):(\d{2})"                  # HH:MM
    r"(?::(\d{2}))?"                       # optional :SS
    r"(?:[Zz]|[+-]\d{2}:\d{2})?"          # optional timezone
    r"$"
)
_TIMESTAMP_RE = re.compile(r"^\d{10}$")   # 10-digit Unix timestamp


def _parse_datetime(value: str) -> tuple[str, str]:
    """Parse datetime string into (date_MM-DD-YYYY, time_HH:MM:SS).

    Accepts::

        "15:35"                            →  (today, 15:35:00)
        "15:35:00"                         →  (today, 15:35:00)
        "15:35:00+08:00"                   →  (today, 15:35:00)
        "2026-06-08T15:35:00+08:00"        →  (06-08-2026, 15:35:00)
        "1759381200"                       →  (date from timestamp, time from timestamp)
    """
    value = value.strip()

    # Unix timestamp (10-digit seconds)
    if _TIMESTAMP_RE.match(value):
        dt = datetime.fromtimestamp(int(value))
        return dt.strftime("%m-%d-%Y"), dt.strftime("%H:%M:%S")

    # RFC 3339
    m = _RFC3339_RE.match(value)
    if not m:
        raise ValueError(
            f"Invalid datetime: {value!r}. "
            f"Expected RFC 3339 (HH:MM, YYYY-MM-DDTHH:MM:SS±TZ) "
            f"or Unix timestamp (seconds)."
        )

    date_str = m.group(1)
    hour, minute, second = m.group(2), m.group(3), m.group(4)

    if date_str:
        y, mo, d = date_str.split("-")
        date_formatted = f"{mo}-{d}-{y}"
    else:
        date_formatted = datetime.now().strftime("%m-%d-%Y")

    time_formatted = f"{int(hour):02d}:{minute}:{second or '00'}"

    # Range validation
    h, m, s = int(hour), int(minute), int(second or "0")
    if not (0 <= h <= 23 and 0 <= m <= 59 and 0 <= s <= 59):
        raise ValueError(
            f"Time out of range: {h:02d}:{m:02d}:{s:02d}. "
            f"Expected 00-23:00-59:00-59."
        )

    return date_formatted, time_formatted


async def route_walk_drive_cycle(
    start_lat: float,
    start_lon: float,
    end_lat: float,
    end_lon: float,
    route_type: str,
) -> dict[str, Any]:
    """Get walking, driving, cycling, or barrier-free route between two points.

    API Reference: https://www.onemap.gov.sg/apidocs/routing

    Args:
        start_lat: Starting point latitude (WGS84).
        start_lon: Starting point longitude (WGS84).
        end_lat: Ending point latitude (WGS84).
        end_lon: Ending point longitude (WGS84).
        route_type: "walk", "drive", "cycle", or "bfa" (barrier-free access).

    Returns:
        JSON dict with route geometry, instructions, distance (meters),
        and time (seconds).

    Raises:
        ValueError: If route_type is not one of the valid options.
    """
    valid_route_types = ("walk", "drive", "cycle", "bfa")
    if route_type not in valid_route_types:
        raise ValueError(
            f"Invalid route_type. Must be one of: {', '.join(valid_route_types)}"
        )

    params: dict[str, Any] = {
        "start": f"{start_lat},{start_lon}",
        "end": f"{end_lat},{end_lon}",
        "routeType": route_type,
    }

    return await _call_api(ROUTING_ENDPOINT, params)


async def route_public_transport(
    start_lat: float,
    start_lon: float,
    end_lat: float,
    end_lon: float,
    departure_time: str,
    mode: str,
    max_walk_distance: int | None = None,
    num_itineraries: int | None = 1,
) -> dict[str, Any]:
    """Get public transport route between two points.

    API Reference: https://www.onemap.gov.sg/apidocs/routing

    Args:
        start_lat: Starting point latitude (WGS84).
        start_lon: Starting point longitude (WGS84).
        end_lat: Ending point latitude (WGS84).
        end_lon: Ending point longitude (WGS84).
        departure_time: Departure datetime.
            RFC 3339: ``"HH:MM"``, ``"HH:MM:SS"``,
            ``"YYYY-MM-DDTHH:MM:SS+08:00"`` (date defaults to today if omitted).
            Unix timestamp (seconds): ``"1759381200"``.
        mode: "TRANSIT" (all), "BUS" (bus only), or "RAIL" (MRT/LRT only).
            Must be UPPERCASE.
        max_walk_distance: Maximum walking distance in meters (optional).
        num_itineraries: Number of routes (1-3, default 1).

    Returns:
        JSON dict with itineraries with legs, transfers, fare, and transit details.

    Raises:
        ValueError: If any parameter validation fails.
    """
    # Validate mode
    valid_modes = ("TRANSIT", "BUS", "RAIL")
    if mode not in valid_modes:
        raise ValueError(
            f"Invalid mode. Must be one of: {', '.join(valid_modes)}"
        )

    # Parse datetime → (MM-DD-YYYY, HH:MM:SS)
    date_formatted, time_formatted = _parse_datetime(departure_time)

    # Validate num_itineraries range
    if num_itineraries is not None and (num_itineraries < 1 or num_itineraries > 3):
        raise ValueError("num_itineraries must be between 1 and 3.")

    params: dict[str, Any] = {
        "start": f"{start_lat},{start_lon}",
        "end": f"{end_lat},{end_lon}",
        "routeType": "pt",
        "date": date_formatted,
        "time": time_formatted,
        "mode": mode,
    }
    if max_walk_distance is not None:
        params["maxWalkDistance"] = max_walk_distance
    if num_itineraries is not None:
        params["numItineraries"] = num_itineraries

    return await _call_api(ROUTING_ENDPOINT, params)
