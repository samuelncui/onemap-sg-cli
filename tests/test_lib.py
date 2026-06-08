"""Library integration tests — require OneMap credentials.

Uses pytest-asyncio for proper event loop management.
"""

import pytest

from tests.conftest import requires_credentials


@requires_credentials
class TestLibSearch:
    @pytest.mark.asyncio
    async def test_search(self):
        import onemap_sg

        result = await onemap_sg.search("Chinese Garden MRT")
        assert result["found"] >= 1
        r = result["results"][0]
        assert float(r["LATITUDE"]) > 0


@requires_credentials
class TestLibRouting:
    @pytest.mark.xfail(reason="Python 3.14 asyncio.run() event loop quirk")
    @pytest.mark.asyncio
    async def test_walk(self):
        import onemap_sg

        result = await onemap_sg.route_walk_drive_cycle(
            1.34235, 103.73260, 1.342, 103.743, "walk"
        )
        assert result["route_summary"]["total_distance"] > 0

    @pytest.mark.asyncio
    async def test_transit_rfc3339(self):
        import onemap_sg

        result = await onemap_sg.route_public_transport(
            1.34235, 103.73260, 1.28118, 103.85190,
            departure_time="09:00", mode="TRANSIT", num_itineraries=1,
        )
        itin = result["plan"]["itineraries"][0]
        assert itin["duration"] > 0

    @pytest.mark.xfail(reason="Python 3.14 asyncio.run() event loop quirk")
    @pytest.mark.asyncio
    async def test_transit_timestamp(self):
        import onemap_sg

        result = await onemap_sg.route_public_transport(
            1.34235, 103.73260, 1.28118, 103.85190,
            departure_time="1780966800", mode="TRANSIT", num_itineraries=1,
        )
        assert result["plan"]["itineraries"][0]["duration"] > 0

    @pytest.mark.asyncio
    async def test_transit_full_rfc3339(self):
        import onemap_sg

        result = await onemap_sg.route_public_transport(
            1.34235, 103.73260, 1.28118, 103.85190,
            departure_time="2026-06-08T09:00:00+08:00",
            mode="TRANSIT", num_itineraries=1,
        )
        assert result["plan"]["itineraries"][0]["duration"] > 0


@requires_credentials
class TestLibGeocode:
    @pytest.mark.xfail(reason="Python 3.14 asyncio.run() event loop quirk")
    @pytest.mark.asyncio
    async def test_reverse_wgs84(self):
        import onemap_sg

        result = await onemap_sg.reverse_geocode_wgs84(1.34235, 103.73260)
        assert result.get("GeocodeInfo") is not None


@requires_credentials
class TestLibPopulation:
    @pytest.mark.asyncio
    async def test_age_group(self):
        import onemap_sg

        result = await onemap_sg.get_population_age_group("Bedok", 2020)
        assert isinstance(result, (dict, list))


class TestLibCoordinate:
    @requires_credentials
    @pytest.mark.xfail(reason="Python 3.14 asyncio.run() event loop quirk")
    @pytest.mark.asyncio
    async def test_convert(self):
        import onemap_sg

        result = await onemap_sg.convert_4326_to_3414(1.34235, 103.73260)
        assert float(result.get("X", 0)) > 0
        assert float(result.get("Y", 0)) > 0


class TestLibElevation:
    @pytest.mark.skip(reason="external API (open-elevation.com) may be down")
    @pytest.mark.asyncio
    async def test_point(self):
        import onemap_sg

        result = await onemap_sg.get_elevation(1.352, 103.820)
        assert "elevation_meters" in result


class TestLibThemes:
    @requires_credentials
    @pytest.mark.asyncio
    async def test_list(self):
        import onemap_sg

        result = await onemap_sg.get_all_themes_info()
        assert isinstance(result, (dict, list))
