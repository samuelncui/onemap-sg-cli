"""
URA Space API client — property transactions, car parks, planning data.
"""

from __future__ import annotations

import os
import json
from datetime import datetime
from typing import Any

import httpx

from onemap_sg._client import _get_async_client

URA_BASE_URL = os.getenv("URA_BASE_URL", "https://eservice.ura.gov.sg/uraDataService")
URA_REQUEST_TIMEOUT = 30.0

URA_DEFAULT_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    ),
    "Accept": "application/json",
    "Accept-Language": "en-US,en;q=0.9",
}

URA_ENDPOINTS = {
    "private_residential_transaction": "PMI_Resi_Transaction",
    "private_residential_rental": "PMI_Resi_Rental",
    "private_residential_median_rental": "PMI_Resi_Rental_Median",
    "private_residential_developer_sales": "PMI_Resi_Developer_Sales",
    "private_residential_pipeline": "PMI_Resi_Pipeline",
    "planning_decisions": "Planning_Decision",
    "car_park_availability": "Car_Park_Availability",
    "car_park_details": "Car_Park_Details",
}


def _get_ura_access_key() -> str:
    access_key = os.getenv("URA_ACCESS_KEY")
    if not access_key:
        raise ValueError(
            "URA_ACCESS_KEY not configured. "
            "Get your access key at https://www.ura.gov.sg/maps/api/"
        )
    return access_key


class URATokenManager:
    """Manages URA daily token lifecycle."""

    def __init__(self) -> None:
        self._daily_token: str | None = None
        self._token_date: datetime | None = None

    def _is_token_valid(self) -> bool:
        if self._daily_token is None or self._token_date is None:
            return False
        return self._token_date.date() == datetime.now().date()

    async def get_daily_token(self, access_key: str) -> str:
        if self._is_token_valid():
            return self._daily_token  # type: ignore[return-value]

        client = await _get_async_client(URA_BASE_URL, URA_REQUEST_TIMEOUT)
        headers = {**URA_DEFAULT_HEADERS, "AccessKey": access_key}

        response = await client.get("/insertNewToken/v1", headers=headers)
        response.raise_for_status()

        data = response.json()
        if data.get("Status") == "Success":
            self._daily_token = data.get("Result")
            self._token_date = datetime.now()
            return self._daily_token  # type: ignore[return-value]
        else:
            raise ValueError(f"Failed to get URA token: {data}")


_ura_token_manager = URATokenManager()


async def _call_ura_api(
    service: str,
    params: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Make an authenticated API call to URA Data Service."""
    access_key = _get_ura_access_key()
    daily_token = await _ura_token_manager.get_daily_token(access_key)

    client = await _get_async_client(URA_BASE_URL, URA_REQUEST_TIMEOUT)

    headers = {
        **URA_DEFAULT_HEADERS,
        "AccessKey": access_key,
        "Token": daily_token,
    }

    endpoint = f"/invokeUraDS/v1?service={service}"
    if params:
        for key, value in params.items():
            endpoint += f"&{key}={value}"

    response = await client.get(endpoint, headers=headers)
    response.raise_for_status()

    try:
        return response.json()
    except Exception:
        content = response.content.decode("latin-1")
        return json.loads(content)


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


async def get_private_residential_transactions(batch: int = 1) -> dict[str, Any]:
    """
    Get private residential property transactions (past 5 years).

    Args:
        batch: Batch number 1-4, split by postal districts:
               1 = districts 01-07, 2 = districts 08-14,
               3 = districts 15-21, 4 = districts 22-28

    Returns:
        Transaction records with price, area, tenure, district info.
    """
    return await _call_ura_api(
        URA_ENDPOINTS["private_residential_transaction"],
        {"batch": str(batch)},
    )


async def get_private_rental_contracts(ref_period: str = "25q4") -> dict[str, Any]:
    """
    Get private residential rental contracts (past 5 years).

    Args:
        ref_period: Reference quarter in yyqq format (e.g., '25q1' for 2025 Q1).
    """
    return await _call_ura_api(
        URA_ENDPOINTS["private_residential_rental"],
        {"refPeriod": ref_period},
    )


async def get_median_rentals() -> dict[str, Any]:
    """
    Get median rentals for private non-landed residential properties (past 3 years).
    Returns psf25, median, psf75 values.
    """
    return await _call_ura_api(URA_ENDPOINTS["private_residential_median_rental"])


async def get_developer_sales(ref_period: str = "0925") -> dict[str, Any]:
    """
    Get private residential units sold by developers (past 3 years).

    Args:
        ref_period: Reference month in mmyy format (e.g., '0925' for Sep 2025).
    """
    return await _call_ura_api(
        URA_ENDPOINTS["private_residential_developer_sales"],
        {"refPeriod": ref_period},
    )


async def get_residential_pipeline() -> dict[str, Any]:
    """
    Get private residential projects in the pipeline.
    Returns unit counts by type, expected TOP year, developer.
    """
    return await _call_ura_api(URA_ENDPOINTS["private_residential_pipeline"])


async def get_planning_decisions(year: int = 2025) -> dict[str, Any]:
    """
    Get planning decisions (Written Permission granted/rejected by URA).

    Args:
        year: Year to retrieve (records after 2000 only).
    """
    return await _call_ura_api(
        URA_ENDPOINTS["planning_decisions"],
        {"year": str(year)},
    )


async def get_car_park_availability() -> dict[str, Any]:
    """Get real-time car park availability (updates every 3-5 minutes)."""
    return await _call_ura_api(URA_ENDPOINTS["car_park_availability"])


async def get_car_park_details() -> dict[str, Any]:
    """Get URA car park list and parking rates."""
    return await _call_ura_api(URA_ENDPOINTS["car_park_details"])
