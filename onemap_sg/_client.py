"""
OneMap API client — authentication, token management, base API call.
Internal module. Public API functions are in sibling modules.
"""

from __future__ import annotations

import asyncio
import os
import time
from typing import Any

import httpx
from dotenv import load_dotenv

load_dotenv()

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

TOKEN_REFRESH_BUFFER_SECONDS = 60

BASE_URL = os.getenv("ONEMAP_BASE_URL", "https://www.onemap.gov.sg")
ELEVATION_API_URL = os.getenv(
    "ELEVATION_API_URL", "https://api.open-elevation.com/api/v1/lookup"
)

REQUEST_TIMEOUT = 30.0
JSON_HEADERS = {"Content-Type": "application/json"}

# API Endpoints
AUTH_ENDPOINT = "/api/auth/post/getToken"
SEARCH_ENDPOINT = "/api/common/elastic/search"
REVGEOCODE_WGS84_ENDPOINT = "/api/public/revgeocode"
REVGEOCODE_SVY21_ENDPOINT = "/api/public/revgeocodexy"
ROUTING_ENDPOINT = "/api/public/routingsvc/route"
CONVERT_4326_TO_3857 = "/api/common/convert/4326to3857"
CONVERT_4326_TO_3414 = "/api/common/convert/4326to3414"
CONVERT_3414_TO_3857 = "/api/common/convert/3414to3857"
CONVERT_3414_TO_4326 = "/api/common/convert/3414to4326"
CONVERT_3857_TO_3414 = "/api/common/convert/3857to3414"
CONVERT_3857_TO_4326 = "/api/common/convert/3857to4326"
THEME_CHECK_STATUS = "/api/public/themesvc/checkThemeStatus"
THEME_GET_INFO = "/api/public/themesvc/getThemeInfo"
THEME_GET_ALL_INFO = "/api/public/themesvc/getAllThemesInfo"
THEME_RETRIEVE = "/api/public/themesvc/retrieveTheme"
PLANNING_AREA_ALL = "/api/public/popapi/getAllPlanningarea"
PLANNING_AREA_NAMES = "/api/public/popapi/getPlanningareaNames"
PLANNING_AREA_QUERY = "/api/public/popapi/getPlanningarea"
POP_ECONOMIC_STATUS = "/api/public/popapi/getEconomicStatus"
POP_EDUCATION = "/api/public/popapi/getEducationAttending"
POP_ETHNIC_GROUP = "/api/public/popapi/getEthnicGroup"
POP_HOUSEHOLD_INCOME = "/api/public/popapi/getHouseholdMonthlyIncomeWork"
POP_HOUSEHOLD_SIZE = "/api/public/popapi/getHouseholdSize"
POP_HOUSEHOLD_STRUCTURE = "/api/public/popapi/getHouseholdStructure"
POP_INCOME_FROM_WORK = "/api/public/popapi/getIncomeFromWork"
POP_INDUSTRY = "/api/public/popapi/getIndustry"
POP_LANGUAGE_LITERATE = "/api/public/popapi/getLanguageLiterate"
POP_MARITAL_STATUS = "/api/public/popapi/getMaritalStatus"
POP_TRANSPORT_SCHOOL = "/api/public/popapi/getModeOfTransportSchool"
POP_TRANSPORT_WORK = "/api/public/popapi/getModeOfTransportWork"
POP_AGE_GROUP = "/api/public/popapi/getPopulationAgeGroup"
POP_RELIGION = "/api/public/popapi/getReligion"
POP_SPOKEN_LANGUAGE = "/api/public/popapi/getSpokenAtHome"
POP_TENANCY = "/api/public/popapi/getTenancy"
POP_DWELLING_HOUSEHOLD = "/api/public/popapi/getTypeOfDwellingHousehold"
POP_DWELLING_POP = "/api/public/popapi/getTypeOfDwellingPop"
NEARBY_MRT = "/api/public/nearbysvc/getNearestMrtStops"
NEARBY_BUS = "/api/public/nearbysvc/getNearestBusStops"
STATIC_MAP_ENDPOINT = "/api/staticmap/getStaticImage"


# ---------------------------------------------------------------------------
# HTTP client cache
# ---------------------------------------------------------------------------

_http_clients: dict[str, httpx.AsyncClient] = {}


async def _get_async_client(
    base_url: str, timeout: float = 30.0
) -> httpx.AsyncClient:
    if base_url not in _http_clients:
        _http_clients[base_url] = httpx.AsyncClient(
            base_url=base_url, timeout=timeout
        )
    return _http_clients[base_url]


async def _cleanup_clients() -> None:
    for client in _http_clients.values():
        await client.aclose()
    _http_clients.clear()


# ---------------------------------------------------------------------------
# Token management
# ---------------------------------------------------------------------------


def _get_credentials() -> tuple[str, str]:
    email = os.getenv("ONEMAP_EMAIL")
    password = os.getenv("ONEMAP_EMAIL_PASSWORD")
    if not email or not password:
        raise ValueError(
            "OneMap credentials required. Set ONEMAP_EMAIL and "
            "ONEMAP_EMAIL_PASSWORD environment variables "
            "(or create a .env file)."
        )
    return email, password


def _get_static_token() -> str | None:
    return os.getenv("ONEMAP_TOKEN")


class AccessTokenManager:
    """Manages OneMap access token lifecycle with automatic refresh."""

    def __init__(self) -> None:
        self._access_token: str | None = None
        self._expiry_timestamp: float = 0.0
        self._lock = asyncio.Lock()
        self._use_static_token = False

        static_token = _get_static_token()
        if static_token:
            self._access_token = static_token
            self._expiry_timestamp = time.time() + (365 * 24 * 60 * 60)
            self._use_static_token = True

    def _parse_expiry_timestamp(self, raw_value: Any) -> float:
        try:
            expiry = float(str(raw_value).strip())
        except (TypeError, ValueError) as exc:
            raise ValueError("Invalid expiry timestamp in token response.") from exc
        if expiry > 1e11:  # milliseconds
            expiry /= 1000.0
        return expiry

    def _is_token_expired(self) -> bool:
        if self._access_token is None:
            return True
        now = time.time()
        refresh_threshold = self._expiry_timestamp - TOKEN_REFRESH_BUFFER_SECONDS
        return now >= refresh_threshold

    async def refresh(self) -> None:
        async with self._lock:
            if not self._is_token_expired() and not self._use_static_token:
                return
            if self._use_static_token:
                self._use_static_token = False

            email, password = _get_credentials()
            client = await _get_async_client(BASE_URL, REQUEST_TIMEOUT)

            response = await client.post(
                AUTH_ENDPOINT,
                json={"email": email, "password": password},
                headers=JSON_HEADERS,
            )
            response.raise_for_status()
            payload = response.json()

            access_token = payload.get("access_token")
            expiry_raw = payload.get("expiry_timestamp")
            if not access_token or expiry_raw is None:
                raise ValueError("Auth response missing token metadata.")

            self._access_token = access_token
            self._expiry_timestamp = self._parse_expiry_timestamp(expiry_raw)

    async def get_access_token(self) -> str:
        if self._is_token_expired():
            await self.refresh()
        if self._access_token is None:
            raise RuntimeError("Token refresh failed without error.")
        return self._access_token


_token_manager = AccessTokenManager()


# ---------------------------------------------------------------------------
# Base API call
# ---------------------------------------------------------------------------


async def _call_api(
    endpoint: str,
    params: dict[str, Any] | None = None,
    *,
    _retry_on_auth_error: bool = True,
) -> dict[str, Any]:
    """Make an authenticated GET request to OneMap. Returns parsed JSON."""
    try:
        access_token = await _token_manager.get_access_token()
        client = await _get_async_client(BASE_URL, REQUEST_TIMEOUT)

        response = await client.get(
            endpoint,
            params=params,
            headers={"Authorization": access_token},
        )
        response.raise_for_status()
        return response.json()
    except httpx.HTTPStatusError as exc:
        if exc.response.status_code == 401 and _retry_on_auth_error:
            await _token_manager.refresh()
            return await _call_api(endpoint, params, _retry_on_auth_error=False)
        raise
