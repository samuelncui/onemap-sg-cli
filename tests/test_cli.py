"""CLI integration tests — require OneMap credentials."""

import json

import pytest

from tests.conftest import onemap_cli, requires_credentials


def _cli_json(*args: str) -> dict:
    """Run CLI and parse JSON output."""
    result = onemap_cli(*args)
    if result.returncode != 0:
        pytest.fail(f"CLI failed (exit {result.returncode}): {result.stderr[:500]}")
    return json.loads(result.stdout)


class TestSearch:
    @requires_credentials
    def test_search_mrt(self):
        data = _cli_json("search", "Chinese Garden MRT")
        assert data["found"] >= 1
        r = data["results"][0]
        assert "CHINESE GARDEN" in r["BUILDING"]

    @requires_credentials
    def test_search_postal(self):
        data = _cli_json("search", "609959")
        assert data["found"] >= 1


class TestRouteTransit:
    @requires_credentials
    def test_by_address(self):
        data = _cli_json(
            "route", "transit",
            "Chinese Garden MRT", "One Raffles Quay",
            "--num", "1",
        )
        plan = data["plan"]
        assert len(plan["itineraries"]) >= 1
        itin = plan["itineraries"][0]
        assert itin["duration"] > 0

    @requires_credentials
    def test_by_latlon(self):
        data = _cli_json(
            "route", "transit",
            "1.342,103.732", "1.281,103.852",
            "--num", "1",
        )
        assert data["plan"]["itineraries"][0]["duration"] > 0

    @requires_credentials
    def test_rfc3339_time(self):
        data = _cli_json(
            "route", "transit",
            "1.342,103.732", "1.281,103.852",
            "--time", "09:00", "--num", "1",
        )
        assert data["plan"]["itineraries"][0]["duration"] > 0

    @requires_credentials
    def test_unix_timestamp(self):
        data = _cli_json(
            "route", "transit",
            "1.342,103.732", "1.281,103.852",
            "--time", "1780966800", "--num", "1",
        )
        assert data["plan"]["itineraries"][0]["duration"] > 0

    @requires_credentials
    def test_rail_only(self):
        data = _cli_json(
            "route", "transit",
            "1.342,103.732", "1.281,103.852",
            "--mode", "RAIL", "--num", "1",
        )
        itin = data["plan"]["itineraries"][0]
        # RAIL mode should have subway legs
        modes = {leg["mode"] for leg in itin["legs"]}
        assert "SUBWAY" in modes


class TestRouteWalk:
    @requires_credentials
    def test_walk_by_address(self):
        data = _cli_json("route", "walk", "Chinese Garden MRT", "Jurong East MRT")
        summary = data.get("route_summary", {})
        assert summary.get("total_distance", 0) > 0


class TestGeocode:
    @requires_credentials
    def test_wgs84(self):
        data = _cli_json("geocode", "wgs84", "1.34235", "103.73260")
        assert data.get("GeocodeInfo") is not None

    @requires_credentials
    def test_svy21(self):
        data = _cli_json("geocode", "svy21", "16790", "36056")
        assert data.get("GeocodeInfo") is not None


class TestThemes:
    @requires_credentials
    def test_list_themes(self):
        data = _cli_json("theme", "list")
        assert "ThemeList" in data or "themes" in str(data).lower()

    @requires_credentials
    def test_theme_info(self):
        data = _cli_json("theme", "info", "kindergartens")
        assert data.get("Category") or data.get("THEMENAME")

    @requires_credentials
    def test_retrieve_theme(self):
        data = _cli_json(
            "theme", "get", "kindergartens",
            "--extents", "1.29,103.78,1.33,103.87",
        )
        assert "SrchResults" in data


class TestCoordinate:
    @requires_credentials
    def test_wgs84_to_svy21(self):
        data = _cli_json("convert", "wgs84-to-svy21", "1.34235", "103.73260")
        assert "X" in data and "Y" in data

    @requires_credentials
    def test_svy21_to_wgs84(self):
        data = _cli_json("convert", "svy21-to-wgs84", "16790", "36056")
        assert "latitude" in data and "longitude" in data


class TestPlanning:
    @requires_credentials
    def test_names(self):
        data = _cli_json("planning", "names")
        names = data if isinstance(data, list) else data.get("data", [])
        assert len(names) > 0

    @requires_credentials
    def test_locate(self):
        data = _cli_json("planning", "locate", "1.342", "103.732")
        # Response varies; just check it doesn't error
        assert isinstance(data, (dict, list))


class TestElevation:
    # Open-Elevation is an external free API — may be unavailable
    @pytest.mark.skip(reason="external API (open-elevation.com) may be down")
    def test_point(self):
        data = _cli_json("elevation", "point", "1.352", "103.820")
        assert "elevation_meters" in data

    @pytest.mark.skip(reason="external API (open-elevation.com) may be down")
    def test_profile(self):
        data = _cli_json("elevation", "profile", "1.35,103.82|1.36,103.83|1.37,103.84")
        assert data.get("point_count", 0) >= 2
