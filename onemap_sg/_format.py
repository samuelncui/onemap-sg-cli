"""
Output formatting for onemap CLI.
Converts raw API results into text, simplified JSON, or raw JSON.
"""

from __future__ import annotations

import json
from typing import Any


def format_output(raw: dict[str, Any], category: str, fmt: str) -> str:
    """Format CLI output based on format mode.

    Args:
        raw: Raw API response dict.
        category: Command category (search, transit, walk, geocode, etc.).
        fmt: "text", "json", or "raw-json".
    """
    if fmt == "raw-json":
        return json.dumps(raw, indent=2, ensure_ascii=False)

    simplified = _simplify(raw, category)

    if fmt == "json":
        return json.dumps(simplified, indent=2, ensure_ascii=False)

    return _to_text(simplified, category)


# ── Simplifiers ──


def _simplify(raw: Any, category: str) -> Any:
    """Reduce raw API response to essential fields."""
    if category == "search":
        return [_simplify_search(r) for r in raw.get("results", [])]
    if category in ("walk", "drive", "cycle"):
        return _simplify_route_summary(raw)
    if category == "transit":
        return _simplify_transit(raw)
    if category == "geocode":
        return _simplify_geocode(raw)
    if category in ("convert", "themes-list", "theme-info", "theme-get",
                    "planning", "pop", "nearby", "amenity",
                    "elevation", "map", "ura"):
        return raw  # These are already compact or need full output
    return raw


def _simplify_search(r: dict) -> dict:
    return {
        "name": r.get("BUILDING") or r.get("ROAD_NAME", ""),
        "address": r.get("ADDRESS", ""),
        "postal": r.get("POSTAL", ""),
        "lat": float(r.get("LATITUDE", 0)),
        "lon": float(r.get("LONGITUDE", 0)),
    }


def _simplify_route_summary(raw: dict) -> dict:
    s = raw.get("route_summary", {})
    return {
        "distance_m": s.get("total_distance"),
        "time_s": s.get("total_time"),
        "time_min": round(s.get("total_time", 0) / 60, 1) if s.get("total_time") else None,
    }


def _simplify_transit(raw: dict) -> dict:
    itin = raw.get("plan", {}).get("itineraries", [{}])[0]
    legs = []
    for leg in itin.get("legs", []):
        mode = leg.get("mode", "?")
        if mode == "WALK":
            legs.append({
                "mode": "walk",
                "distance_m": leg.get("distance"),
            })
        else:
            legs.append({
                "mode": mode.lower(),
                "route": leg.get("route"),
                "from": leg.get("from", {}).get("name"),
                "to": leg.get("to", {}).get("name"),
                "stops": leg.get("intermediateStops", 1) - 1 if isinstance(leg.get("intermediateStops"), int) else None,
            })
    fare = itin.get("fare", {})
    fare_cents = None
    if isinstance(fare, dict):
        fc = fare.get("fare", {})
        if isinstance(fc, dict):
            fare_cents = fc.get("regular", {}).get("cents")
    return {
        "duration_min": round(itin.get("duration", 0) / 60, 1),
        "transfers": itin.get("transfers", 0),
        "fare_cents": fare_cents,
        "legs": legs,
    }


def _simplify_geocode(raw: dict) -> dict:
    info = raw.get("GeocodeInfo", [{}])[0] if isinstance(raw.get("GeocodeInfo"), list) else raw.get("GeocodeInfo", {})
    return {
        "address": info.get("BUILDINGNAME") or info.get("ROAD", ""),
        "postal": info.get("POSTALCODE", ""),
    }


# ── Text formatters ──


def _to_text(data: Any, category: str) -> str:
    """Render simplified dict to readable text."""
    if category == "search":
        return _text_search(data)
    if category in ("walk", "drive", "cycle"):
        return _text_route(data, category)
    if category == "transit":
        return _text_transit(data)
    if category == "geocode":
        return _text_geocode(data)
    if category == "elevation":
        return _text_elevation(data)
    if category == "nearby":
        return _text_nearby(data, category)
    # Fallback: pretty-print JSON
    return json.dumps(data, indent=2, ensure_ascii=False)


def _text_search(results: list) -> str:
    lines = []
    for r in results[:10]:
        lines.append(f"{r['name']}")
        lines.append(f"  {r['address']}")
        lines.append(f"  postal={r['postal']}  lat={r['lat']:.6f}  lon={r['lon']:.6f}")
        lines.append("")
    if len(results) > 10:
        lines.append(f"... and {len(results) - 10} more results")
    return "\n".join(lines).strip()


def _text_route(data: dict, category: str) -> str:
    mode = {"walk": "Walking", "drive": "Driving", "cycle": "Cycling"}.get(category, category)
    return f"{mode} route: {data['distance_m']}m, {data['time_min']} min"


def _text_transit(data: dict) -> str:
    lines = [
        f"Duration: {data['duration_min']} min  |  Transfers: {data['transfers']}",
    ]
    if data["fare_cents"]:
        lines[-1] += f"  |  Fare: ${data['fare_cents'] / 100:.2f}"
    for leg in data["legs"]:
        if leg["mode"] == "walk":
            lines.append(f"  Walk {leg['distance_m']}m")
        else:
            lines.append(f"  {leg['route']} ({leg['from']} → {leg['to']})")
    return "\n".join(lines)


def _text_geocode(data: dict) -> str:
    return f"{data['address']}\npostal: {data['postal']}"


def _text_elevation(data: dict) -> str:
    return f"Elevation: {data.get('elevation_meters', '?')}m"


def _text_nearby(data: dict, category: str) -> str:
    items = data.get("data", data.get("results", data))
    if isinstance(items, dict):
        items = [items]
    if not isinstance(items, list):
        return json.dumps(data, indent=2, ensure_ascii=False)
    lines = []
    for item in items[:10]:
        name = item.get("name", item.get("NAME", item.get("station_name", item.get("Description", "?"))))
        dist = item.get("distance_meters", item.get("distance", ""))
        lines.append(f"  {name}" + (f"  ({dist}m)" if dist else ""))
    if len(items) > 10:
        lines.append(f"  ... and {len(items) - 10} more")
    return "\n".join(lines)
