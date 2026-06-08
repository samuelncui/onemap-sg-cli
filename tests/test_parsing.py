"""Unit tests for time parsing — no network calls."""

import pytest
from onemap_sg.routing import _parse_datetime


class TestParseDatetime:
    """_parse_datetime returns (MM-DD-YYYY, HH:MM:SS)."""

    def test_rfc3339_time_only(self):
        date_str, time_str = _parse_datetime("09:00")
        assert time_str == "09:00:00"
        assert len(date_str) == 10  # MM-DD-YYYY

    def test_rfc3339_time_with_seconds(self):
        _, time_str = _parse_datetime("15:35:00")
        assert time_str == "15:35:00"

    def test_rfc3339_time_shorthand(self):
        _, time_str = _parse_datetime("9:05")
        assert time_str == "09:05:00"

    def test_rfc3339_time_with_tz(self):
        _, time_str = _parse_datetime("15:35:00+08:00")
        assert time_str == "15:35:00"

    def test_rfc3339_time_utc_z(self):
        _, time_str = _parse_datetime("15:35:00Z")
        assert time_str == "15:35:00"

    def test_rfc3339_full_datetime(self):
        date_str, time_str = _parse_datetime("2026-06-08T09:00:00+08:00")
        assert date_str == "06-08-2026"
        assert time_str == "09:00:00"

    def test_unix_timestamp(self):
        date_str, time_str = _parse_datetime("1780966800")  # 2026-06-09 01:00 UTC
        assert date_str == "06-09-2026"
        assert time_str in ("01:00:00", "09:00:00")  # depends on CI timezone

    def test_invalid_rejected(self):
        with pytest.raises(ValueError):
            _parse_datetime("not-a-time")

        with pytest.raises(ValueError):
            _parse_datetime("25:99")  # hour out of range

        with pytest.raises(ValueError):
            _parse_datetime("12:60")  # minute out of range

        with pytest.raises(ValueError):
            _parse_datetime("")  # empty
