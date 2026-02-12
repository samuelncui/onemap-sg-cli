"""
OneMap MCP Server v2
A Model Context Protocol server that provides access to Singapore's OneMap APIs.

This server implements tools for:
- Search: Address and location search
- Reverse Geocode: Convert coordinates to addresses (WGS84 and SVY21)
- Routing: Public transport, driving, walking, cycling, barrier-free routes
- Coordinate Converters: EPSG 4326 (WGS84), EPSG 3414 (SVY21), EPSG 3857
- Themes: Access thematic layers for locations, amenities, boundaries, etc.
- Planning Area: Singapore planning area information
- Population Query: Demographics and statistics by planning area
- Nearby Transport: Find nearby MRT/LRT stations and bus stops
- Static Map: Generate static map images with optional overlays
"""

import asyncio
import base64
import os
import re
import time
from typing import Any, Dict, Tuple

import httpx
import utils
import ura_client
import uvicorn
from dotenv import load_dotenv
from mcp.server.fastmcp import FastMCP

load_dotenv()

# Constants
TOKEN_REFRESH_BUFFER_SECONDS = 60  # Refresh token 60 seconds before expiry

# Base configuration
BASE_URL = os.getenv("ONEMAP_BASE_URL", "https://www.onemap.gov.sg")
REQUEST_TIMEOUT = 30.0
JSON_HEADERS = {"Content-Type": "application/json"}

# External APIs
ELEVATION_API_URL = os.getenv("ELEVATION_API_URL", "https://api.open-elevation.com/api/v1/lookup")

# API Endpoints
AUTH_ENDPOINT = "/api/auth/post/getToken"
SEARCH_ENDPOINT = "/api/common/elastic/search"

# Reverse Geocode
REVGEOCODE_WGS84_ENDPOINT = "/api/public/revgeocode"
REVGEOCODE_SVY21_ENDPOINT = "/api/public/revgeocodexy"

# Routing
ROUTING_ENDPOINT = "/api/public/routingsvc/route"

# Coordinate Converters
CONVERT_4326_TO_3857 = "/api/common/convert/4326to3857"
CONVERT_4326_TO_3414 = "/api/common/convert/4326to3414"
CONVERT_3414_TO_3857 = "/api/common/convert/3414to3857"
CONVERT_3414_TO_4326 = "/api/common/convert/3414to4326"
CONVERT_3857_TO_3414 = "/api/common/convert/3857to3414"
CONVERT_3857_TO_4326 = "/api/common/convert/3857to4326"

# Themes
THEME_CHECK_STATUS = "/api/public/themesvc/checkThemeStatus"
THEME_GET_INFO = "/api/public/themesvc/getThemeInfo"
THEME_GET_ALL_INFO = "/api/public/themesvc/getAllThemesInfo"
THEME_RETRIEVE = "/api/public/themesvc/retrieveTheme"

# Planning Area
PLANNING_AREA_ALL = "/api/public/popapi/getAllPlanningarea"
PLANNING_AREA_NAMES = "/api/public/popapi/getPlanningareaNames"
PLANNING_AREA_QUERY = "/api/public/popapi/getPlanningarea"

# Population Query
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

# Nearby Transport
NEARBY_MRT = "/api/public/nearbysvc/getNearestMrtStops"
NEARBY_BUS = "/api/public/nearbysvc/getNearestBusStops"

# Static Map
STATIC_MAP_ENDPOINT = "/api/staticmap/getStaticImage"

# Import TransportSecuritySettings to disable DNS rebinding protection for cloud deployment
from mcp.server.transport_security import TransportSecuritySettings

# Create transport security settings that allow all hosts (for Azure Container Apps)
transport_security = TransportSecuritySettings(
    enable_dns_rebinding_protection=False,  # Disable for cloud deployment
)

mcp = FastMCP(
    "onemap-v2",
    stateless_http=True,  # Recommended for production deployments
    json_response=True,   # Return JSON instead of SSE streaming
    dependencies=["httpx", "python-dotenv"],
    transport_security=transport_security,  # Allow all hosts for cloud deployment
)


def _get_credentials() -> Tuple[str, str]:
    """Get OneMap credentials from environment variables."""
    email = os.getenv("ONEMAP_EMAIL")
    password = os.getenv("ONEMAP_EMAIL_PASSWORD")
    if not email or not password:
        raise ValueError(
            "OneMap credentials are required. Set ONEMAP_EMAIL and "
            "ONEMAP_EMAIL_PASSWORD environment variables."
        )
    return email, password


def _get_static_token() -> str | None:
    """Get static token from environment if available."""
    return os.getenv("ONEMAP_TOKEN")


class AccessTokenManager:
    """Manages OneMap access token lifecycle with automatic refresh."""

    def __init__(self) -> None:
        self._access_token: str | None = None
        self._expiry_timestamp: float = 0.0  # Unix epoch in seconds
        self._lock = asyncio.Lock()
        self._use_static_token = False
        
        # Check for static token first
        static_token = _get_static_token()
        if static_token:
            self._access_token = static_token
            # Set expiry far in the future for static tokens (user manages expiry)
            self._expiry_timestamp = time.time() + (365 * 24 * 60 * 60)  # 1 year
            self._use_static_token = True

    def _parse_expiry_timestamp(self, raw_value: Any) -> float:
        """
        Parse and normalize the expiry timestamp from the API response.

        OneMap returns expiry_timestamp as a Unix epoch. It could be in:
        - Seconds (e.g., 1732723200 for ~2024)
        - Milliseconds (e.g., 1732723200000)

        We detect milliseconds if the value exceeds 1e11 (year ~5138 in seconds,
        but year ~1973 in milliseconds - so any current timestamp in ms will
        exceed this).
        """
        try:
            expiry = float(str(raw_value).strip())
        except (TypeError, ValueError) as exc:
            msg = "Token response contained an invalid expiry timestamp."
            raise ValueError(msg) from exc

        # Detect and convert milliseconds to seconds
        # Current epoch in seconds is ~1.7 billion, in ms it's ~1.7 trillion
        if expiry > 1e11:  # More than 100 billion = definitely milliseconds
            expiry /= 1000.0

        return expiry

    def _is_token_expired(self) -> bool:
        """
        Check if the token is expired or will expire soon.

        Returns True if:
        - No token exists
        - Current time >= (expiry_timestamp - buffer)
        """
        if self._access_token is None:
            return True

        now = time.time()
        # Refresh if we're within the buffer period before expiry
        refresh_threshold = self._expiry_timestamp - TOKEN_REFRESH_BUFFER_SECONDS
        return now >= refresh_threshold

    async def refresh(self) -> None:
        """Refresh the access token from OneMap API."""
        async with self._lock:
            # Double-check inside lock to prevent thundering herd
            if not self._is_token_expired() and not self._use_static_token:
                return
            
            # If using static token that might have expired, switch to email/password
            if self._use_static_token:
                self._use_static_token = False

            email, password = _get_credentials()
            client = await utils.get_async_client(BASE_URL, REQUEST_TIMEOUT)

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
                msg = "Authentication response is missing token metadata."
                raise ValueError(msg)

            self._access_token = access_token
            self._expiry_timestamp = self._parse_expiry_timestamp(expiry_raw)

    async def get_access_token(self) -> str:
        """Get a valid access token, refreshing if necessary."""
        if self._is_token_expired():
            await self.refresh()
        if self._access_token is None:
            raise RuntimeError("Token refresh failed without error.")
        return self._access_token


# Global token manager instance
token_manager = AccessTokenManager()


async def _call_api(
    endpoint: str,
    params: Dict[str, Any] | None = None,
    _retry_on_auth_error: bool = True,
) -> str:
    """Make an authenticated API call to OneMap."""
    try:
        access_token = await token_manager.get_access_token()
        client = await utils.get_async_client(BASE_URL, REQUEST_TIMEOUT)

        response = await client.get(
            endpoint,
            params=params,
            headers={"Authorization": access_token},
        )
        response.raise_for_status()
        return utils.format_response(utils.success_response(response.json()))
    except httpx.HTTPStatusError as exc:
        # Handle 401 Unauthorized - token may have expired
        if exc.response.status_code == 401 and _retry_on_auth_error:
            # Force token refresh and retry once
            await token_manager.refresh()
            return await _call_api(endpoint, params, _retry_on_auth_error=False)
        return utils.format_response(utils.handle_http_error(exc))
    except httpx.HTTPError as exc:
        return utils.format_response(utils.handle_http_error(exc))


# =============================================================================
# SEARCH API
# =============================================================================


@mcp.tool()
async def search(
    search_value: str,
    return_geometry: str = "Y",
    get_address_details: str = "Y",
    page_number: int = None,
) -> str:
    """
    Search for address information for roads, buildings, postal codes, etc.

    This API takes a text input (building name, road name, bus stop number, or
    postal code) and returns address information including coordinates.

    API Reference: https://www.onemap.gov.sg/apidocs/search

    Args:
        search_value: Keywords to search (e.g., "Revenue House", "307987", "Orchard Road").
            Cannot be empty.
        return_geometry: "Y" to return geometry/coordinates, "N" otherwise
        get_address_details: "Y" to return detailed address info, "N" otherwise
        page_number: Optional page number for paginated results (must be positive integer)

    Returns:
        JSON with search results including address, coordinates, postal code, etc.
    """
    # Validate search_value is not empty
    if not search_value or not search_value.strip():
        return utils.format_response(
            {
                "success": False,
                "error": "Parameter searchVal is invalid. Cannot be empty.",
            }
        )

    # Validate return_geometry
    if return_geometry not in ["Y", "N"]:
        return utils.format_response(
            {
                "success": False,
                "error": "Invalid return_geometry value. Must be 'Y' or 'N'.",
            }
        )

    # Validate get_address_details
    if get_address_details not in ["Y", "N"]:
        return utils.format_response(
            {
                "success": False,
                "error": "Invalid get_address_details value. Must be 'Y' or 'N'.",
            }
        )

    # Validate page_number if provided
    if page_number is not None and page_number < 1:
        return utils.format_response(
            {
                "success": False,
                "error": "Please state a valid page number. Must be a positive integer.",
            }
        )

    params: Dict[str, Any] = {
        "searchVal": search_value,
        "returnGeom": return_geometry,
        "getAddrDetails": get_address_details,
    }
    if page_number is not None:
        params["pageNum"] = page_number
    return await _call_api(SEARCH_ENDPOINT, params)


# =============================================================================
# REVERSE GEOCODE APIs
# =============================================================================


@mcp.tool()
async def reverse_geocode_wgs84(
    latitude: float,
    longitude: float,
    buffer: int = None,
    address_type: str = None,
) -> str:
    """
    Get address information for a location using WGS84 coordinates (lat/lon).

    Returns addresses within a specified buffer/radius of the location.
    Maximum buffer is 500m for buildings and 20m for roads.

    API Reference: https://www.onemap.gov.sg/apidocs/reverseGeocode

    Args:
        latitude: Latitude in WGS84 format (e.g., 1.3254295)
        longitude: Longitude in WGS84 format (e.g., 103.9005321)
        buffer: Optional radius in meters (0-500). Default searches nearby.
        address_type: "HDB" for HDB properties only, "All" for all property types

    Returns:
        JSON with geocoded address information including building name, road, postal code
    """
    # Validate buffer range
    if buffer is not None and (buffer < 0 or buffer > 500):
        return utils.format_response(
            {"success": False, "error": "Buffer must be between 0 and 500 meters."}
        )

    # Validate address_type
    if address_type is not None and address_type not in ["HDB", "All"]:
        return utils.format_response(
            {"success": False, "error": "Invalid address_type. Must be 'HDB' or 'All'."}
        )

    params: Dict[str, Any] = {"location": f"{latitude},{longitude}"}
    if buffer is not None:
        params["buffer"] = buffer
    if address_type is not None:
        params["addressType"] = address_type
    return await _call_api(REVGEOCODE_WGS84_ENDPOINT, params)


@mcp.tool()
async def reverse_geocode_svy21(
    x: float,
    y: float,
    buffer: int = None,
    address_type: str = None,
) -> str:
    """
    Get address information for a location using SVY21 coordinates (X/Y).

    Returns addresses within a specified buffer/radius of the location.
    Maximum buffer is 500m for buildings and 20m for roads.

    API Reference: https://www.onemap.gov.sg/apidocs/reverseGeocode

    Args:
        x: X coordinate in SVY21 format (e.g., 24291.97788882387)
        y: Y coordinate in SVY21 format (e.g., 31373.0117224489)
        buffer: Optional radius in meters (0-500). Default searches nearby.
        address_type: "HDB" for HDB properties only, "All" for all property types

    Returns:
        JSON with geocoded address information including building name, road, postal code
    """
    # Validate buffer range
    if buffer is not None and (buffer < 0 or buffer > 500):
        return utils.format_response(
            {"success": False, "error": "Buffer must be between 0 and 500 meters."}
        )

    # Validate address_type
    if address_type is not None and address_type not in ["HDB", "All"]:
        return utils.format_response(
            {"success": False, "error": "Invalid address_type. Must be 'HDB' or 'All'."}
        )

    params: Dict[str, Any] = {"location": f"{x},{y}"}
    if buffer is not None:
        params["buffer"] = buffer
    if address_type is not None:
        params["addressType"] = address_type
    return await _call_api(REVGEOCODE_SVY21_ENDPOINT, params)


# =============================================================================
# ROUTING APIs
# =============================================================================


@mcp.tool()
async def route_walk_drive_cycle(
    start_lat: float,
    start_lon: float,
    end_lat: float,
    end_lon: float,
    route_type: str,
) -> str:
    """
    Get walking, driving, cycling, or barrier-free route between two points.

    API Reference: https://www.onemap.gov.sg/apidocs/routing

    Args:
        start_lat: Starting point latitude (WGS84)
        start_lon: Starting point longitude (WGS84)
        end_lat: Ending point latitude (WGS84)
        end_lon: Ending point longitude (WGS84)
        route_type: "walk", "drive", "cycle", or "bfa" (barrier-free access)

    Returns:
        JSON with route geometry, instructions, distance (meters), and time (seconds)
    """
    # Validate route_type
    valid_route_types = ["walk", "drive", "cycle", "bfa"]
    if route_type not in valid_route_types:
        return utils.format_response(
            {
                "success": False,
                "error": f"Invalid route_type. Must be one of: {', '.join(valid_route_types)}",
            }
        )

    params = {
        "start": f"{start_lat},{start_lon}",
        "end": f"{end_lat},{end_lon}",
        "routeType": route_type,
    }
    return await _call_api(ROUTING_ENDPOINT, params)


@mcp.tool()
async def route_public_transport(
    start_lat: float,
    start_lon: float,
    end_lat: float,
    end_lon: float,
    date: str,
    departure_time: str,
    mode: str,
    max_walk_distance: int = None,
    num_itineraries: int = None,
) -> str:
    """
    Get public transport route between two points.

    API Reference: https://www.onemap.gov.sg/apidocs/routing

    Args:
        start_lat: Starting point latitude (WGS84)
        start_lon: Starting point longitude (WGS84)
        end_lat: Ending point latitude (WGS84)
        end_lon: Ending point longitude (WGS84)
        date: Date in MM-DD-YYYY format (e.g., "11-10-2025")
        departure_time: Time in HHMMSS 24-hour format (e.g., "111947")
        mode: "TRANSIT" (all), "BUS" (bus only), or "RAIL" (MRT/LRT only). Must be UPPERCASE.
        max_walk_distance: Maximum walking distance in meters (optional)
        num_itineraries: Number of route options to return (1-3, optional)

    Returns:
        JSON with itineraries with legs, transfers, fare, and transit details
    """
    # Validate mode
    valid_modes = ["TRANSIT", "BUS", "RAIL"]
    if mode not in valid_modes:
        return utils.format_response(
            {
                "success": False,
                "error": f"Invalid mode. Must be one of: {', '.join(valid_modes)}",
            }
        )

    # Validate date format (MM-DD-YYYY)
    if not re.match(r"^\d{2}-\d{2}-\d{4}$", date):
        return utils.format_response(
            {"success": False, "error": "Date format should be in MM-DD-YYYY."}
        )

    # Validate time format (HHMMSS)
    if not re.match(r"^\d{6}$", departure_time):
        return utils.format_response(
            {
                "success": False,
                "error": "Time format should be in HHMMSS (6 digits, 24-hour format).",
            }
        )

    # Validate numItineraries range
    if num_itineraries is not None and (num_itineraries < 1 or num_itineraries > 3):
        return utils.format_response(
            {"success": False, "error": "numItineraries must be between 1 and 3."}
        )

    params: Dict[str, Any] = {
        "start": f"{start_lat},{start_lon}",
        "end": f"{end_lat},{end_lon}",
        "routeType": "pt",
        "date": date,
        "time": departure_time,
        "mode": mode,
    }
    if max_walk_distance is not None:
        params["maxWalkDistance"] = max_walk_distance
    if num_itineraries is not None:
        params["numItineraries"] = num_itineraries
    return await _call_api(ROUTING_ENDPOINT, params)


# =============================================================================
# COORDINATE CONVERTER APIs
# =============================================================================


@mcp.tool()
async def convert_4326_to_3857(latitude: float, longitude: float) -> str:
    """
    Convert coordinates from EPSG:4326 (WGS84) to EPSG:3857 (Web Mercator).

    API Reference: https://www.onemap.gov.sg/apidocs/coordinate

    Args:
        latitude: Latitude in WGS84 format
        longitude: Longitude in WGS84 format

    Returns:
        JSON with X and Y coordinates in EPSG:3857 format
    """
    return await _call_api(
        CONVERT_4326_TO_3857, {"latitude": latitude, "longitude": longitude}
    )


@mcp.tool()
async def convert_4326_to_3414(latitude: float, longitude: float) -> str:
    """
    Convert coordinates from EPSG:4326 (WGS84) to EPSG:3414 (SVY21).

    API Reference: https://www.onemap.gov.sg/apidocs/coordinate

    Args:
        latitude: Latitude in WGS84 format
        longitude: Longitude in WGS84 format

    Returns:
        JSON with X and Y coordinates in SVY21 format
    """
    return await _call_api(
        CONVERT_4326_TO_3414, {"latitude": latitude, "longitude": longitude}
    )


@mcp.tool()
async def convert_3414_to_3857(x: float, y: float) -> str:
    """
    Convert coordinates from EPSG:3414 (SVY21) to EPSG:3857 (Web Mercator).

    API Reference: https://www.onemap.gov.sg/apidocs/coordinate

    Args:
        x: X coordinate in SVY21 format
        y: Y coordinate in SVY21 format

    Returns:
        JSON with X and Y coordinates in EPSG:3857 format
    """
    return await _call_api(CONVERT_3414_TO_3857, {"X": x, "Y": y})


@mcp.tool()
async def convert_3414_to_4326(x: float, y: float) -> str:
    """
    Convert coordinates from EPSG:3414 (SVY21) to EPSG:4326 (WGS84).

    API Reference: https://www.onemap.gov.sg/apidocs/coordinate

    Args:
        x: X coordinate in SVY21 format
        y: Y coordinate in SVY21 format

    Returns:
        JSON with latitude and longitude in WGS84 format
    """
    return await _call_api(CONVERT_3414_TO_4326, {"X": x, "Y": y})


@mcp.tool()
async def convert_3857_to_3414(x: float, y: float) -> str:
    """
    Convert coordinates from EPSG:3857 (Web Mercator) to EPSG:3414 (SVY21).

    API Reference: https://www.onemap.gov.sg/apidocs/coordinate

    Args:
        x: X coordinate in EPSG:3857 format
        y: Y coordinate in EPSG:3857 format

    Returns:
        JSON with X and Y coordinates in SVY21 format
    """
    return await _call_api(CONVERT_3857_TO_3414, {"X": x, "Y": y})


@mcp.tool()
async def convert_3857_to_4326(x: float, y: float) -> str:
    """
    Convert coordinates from EPSG:3857 (Web Mercator) to EPSG:4326 (WGS84).

    API Reference: https://www.onemap.gov.sg/apidocs/coordinate

    Args:
        x: X coordinate in EPSG:3857 format
        y: Y coordinate in EPSG:3857 format

    Returns:
        JSON with latitude and longitude in WGS84 format
    """
    return await _call_api(CONVERT_3857_TO_4326, {"X": x, "Y": y})


# =============================================================================
# THEMES APIs
# =============================================================================


@mcp.tool()
async def get_all_themes_info(more_info: str = "N") -> str:
    """
    Get a list of all available thematic layers in OneMap.

    OneMap has over 100 thematic layers provided by various government agencies,
    including locations for amenities, boundaries, facilities, etc.

    API Reference: https://www.onemap.gov.sg/apidocs/themes

    Args:
        more_info: "Y" to include icon names, category names, and theme owners

    Returns:
        JSON with list of themes including THEMENAME and QUERYNAME
    """
    # Validate more_info
    if more_info not in ["Y", "N"]:
        return utils.format_response(
            {
                "success": False,
                "error": "Invalid more_info value. Must be 'Y' or 'N'.",
            }
        )

    return await _call_api(THEME_GET_ALL_INFO, {"moreInfo": more_info})


@mcp.tool()
async def get_theme_info(query_name: str) -> str:
    """
    Get information about a specific theme by its query name.

    API Reference: https://www.onemap.gov.sg/apidocs/themes

    Args:
        query_name: The theme's query name (e.g., "kindergartens", "communityclubs"). Required.

    Returns:
        JSON with theme details including THEMENAME and QUERYNAME
    """
    # Validate query_name is not empty
    if not query_name or not query_name.strip():
        return utils.format_response(
            {"success": False, "error": "There is no query name."}
        )

    return await _call_api(THEME_GET_INFO, {"queryName": query_name})


@mcp.tool()
async def check_theme_status(query_name: str, date_time: str) -> str:
    """
    Check if a theme has been updated since a specific datetime.

    API Reference: https://www.onemap.gov.sg/apidocs/themes

    Args:
        query_name: The theme's query name (e.g., "kindergartens"). Required.
        date_time: DateTime in ISO format (e.g., "2023-06-15T16:00:00.000Z"). Required.

    Returns:
        JSON with UpdatedFile boolean indicating if theme was updated
    """
    # Validate query_name is not empty
    if not query_name or not query_name.strip():
        return utils.format_response(
            {"success": False, "error": "There is no query name."}
        )

    # Validate date_time is not empty
    if not date_time or not date_time.strip():
        return utils.format_response(
            {"success": False, "error": "Your date provided is empty."}
        )

    return await _call_api(
        THEME_CHECK_STATUS, {"queryName": query_name, "dateTime": date_time}
    )


@mcp.tool()
async def retrieve_theme(query_name: str, extents: str = None) -> str:
    """
    Retrieve all data for a specific theme, optionally within a bounding box.

    API Reference: https://www.onemap.gov.sg/apidocs/themes

    Args:
        query_name: The theme's query name (e.g., "dengue_cluster", "kindergartens"). Required.
        extents: Optional bounding box as "lat1,lon1,lat2,lon2"
                 (e.g., "1.291789,103.7796402,1.3290461,103.8726032")

    Returns:
        JSON with theme data including locations, descriptions, and GeoJSON geometries
    """
    # Validate query_name is not empty
    if not query_name or not query_name.strip():
        return utils.format_response(
            {"success": False, "error": "There is no query name."}
        )

    params: Dict[str, Any] = {"queryName": query_name}
    if extents is not None:
        params["extents"] = extents
    return await _call_api(THEME_RETRIEVE, params)


# =============================================================================
# PLANNING AREA APIs
# =============================================================================


VALID_PLANNING_YEARS = [1998, 2008, 2014, 2019]
VALID_POPULATION_YEARS = [2000, 2010, 2015, 2020]


@mcp.tool()
async def get_all_planning_areas(year: int = None) -> str:
    """
    Get all planning area polygons in Singapore.

    Singapore has 55 planning areas delineated by the Urban Redevelopment Authority.

    API Reference: https://www.onemap.gov.sg/apidocs/planningarea

    Args:
        year: Optional year (1998, 2008, 2014, 2019). Defaults to latest.

    Returns:
        JSON with planning area names and GeoJSON polygon geometries
    """
    # Validate year if provided
    if year is not None and year not in VALID_PLANNING_YEARS:
        return utils.format_response(
            {
                "success": False,
                "error": f"Please enter valid year. Valid years are: {VALID_PLANNING_YEARS}",
            }
        )

    params = {"year": year} if year else {}
    return await _call_api(PLANNING_AREA_ALL, params)


@mcp.tool()
async def get_planning_area_names(year: int = None) -> str:
    """
    Get names of all planning areas in Singapore.

    API Reference: https://www.onemap.gov.sg/apidocs/planningarea

    Args:
        year: Optional year (1998, 2008, 2014, 2019). Defaults to latest.

    Returns:
        JSON list of planning area names and IDs
    """
    # Validate year if provided
    if year is not None and year not in VALID_PLANNING_YEARS:
        return utils.format_response(
            {
                "success": False,
                "error": f"Please enter valid year. Valid years are: {VALID_PLANNING_YEARS}",
            }
        )

    params = {"year": year} if year else {}
    return await _call_api(PLANNING_AREA_NAMES, params)


@mcp.tool()
async def get_planning_area_by_location(
    latitude: float,
    longitude: float,
    year: int = None,
) -> str:
    """
    Get the planning area for a specific location.

    API Reference: https://www.onemap.gov.sg/apidocs/planningarea

    Args:
        latitude: Latitude in WGS84 format
        longitude: Longitude in WGS84 format
        year: Optional year (1998, 2008, 2014, 2019). Defaults to latest.

    Returns:
        JSON with planning area name and GeoJSON polygon geometry
    """
    # Validate year if provided
    if year is not None and year not in VALID_PLANNING_YEARS:
        return utils.format_response(
            {
                "success": False,
                "error": f"Please enter valid year. Valid years are: {VALID_PLANNING_YEARS}",
            }
        )

    params: Dict[str, Any] = {"latitude": latitude, "longitude": longitude}
    if year:
        params["year"] = year
    return await _call_api(PLANNING_AREA_QUERY, params)


# =============================================================================
# POPULATION QUERY APIs
# =============================================================================


def _validate_population_params(
    planning_area: str, year: int, gender: str | None = None
) -> str | None:
    """Validate common population query parameters. Returns error string or None."""
    if not planning_area or not planning_area.strip():
        return utils.format_response(
            {"success": False, "error": "Please enter planning area."}
        )
    if year not in VALID_POPULATION_YEARS:
        return utils.format_response(
            {
                "success": False,
                "error": f"Please enter valid year. Valid years are: {VALID_POPULATION_YEARS}",
            }
        )
    if gender is not None and gender.lower() not in ["male", "female"]:
        return utils.format_response(
            {"success": False, "error": "Your gender must be either male or female."}
        )
    return None


@mcp.tool()
async def get_economic_status(
    planning_area: str,
    year: int,
    gender: str = None,
) -> str:
    """
    Get economic status data (employed, unemployed, inactive) for a planning area.

    API Reference: https://www.onemap.gov.sg/apidocs/populationquery

    Args:
        planning_area: Planning area name (e.g., "Bedok", "Tampines"). Required.
        year: Year (2000, 2010, 2015, or 2020). Required.
        gender: Optional "male" or "female" filter

    Returns:
        JSON with employment statistics
    """
    # Validate parameters
    error = _validate_population_params(planning_area, year, gender)
    if error:
        return error

    params: Dict[str, Any] = {"planningArea": planning_area, "year": year}
    if gender:
        params["gender"] = gender
    return await _call_api(POP_ECONOMIC_STATUS, params)


@mcp.tool()
async def get_education_status(planning_area: str, year: int) -> str:
    """
    Get education attending data for a planning area.

    API Reference: https://www.onemap.gov.sg/apidocs/populationquery

    Args:
        planning_area: Planning area name (e.g., "Bedok", "Tampines"). Required.
        year: Year (2000, 2010, 2015, or 2020). Required.

    Returns:
        JSON with education level statistics (pre_primary, primary, secondary, etc.)
    """
    # Validate parameters
    error = _validate_population_params(planning_area, year)
    if error:
        return error

    return await _call_api(POP_EDUCATION, {"planningArea": planning_area, "year": year})


@mcp.tool()
async def get_ethnic_distribution(
    planning_area: str,
    year: int,
    gender: str = None,
) -> str:
    """
    Get ethnic group distribution for a planning area.

    API Reference: https://www.onemap.gov.sg/apidocs/populationquery

    Args:
        planning_area: Planning area name (e.g., "Bedok", "Tampines"). Required.
        year: Year (2000, 2010, 2015, or 2020). Required.
        gender: Optional "male" or "female" filter

    Returns:
        JSON with ethnic distribution (chinese, malays, indian, others)
    """
    # Validate parameters
    error = _validate_population_params(planning_area, year, gender)
    if error:
        return error

    params: Dict[str, Any] = {"planningArea": planning_area, "year": year}
    if gender:
        params["gender"] = gender
    return await _call_api(POP_ETHNIC_GROUP, params)


@mcp.tool()
async def get_household_monthly_income(planning_area: str, year: int) -> str:
    """
    Get monthly household income from work for a planning area.

    API Reference: https://www.onemap.gov.sg/apidocs/populationquery

    Args:
        planning_area: Planning area name (e.g., "Bedok", "Tampines"). Required.
        year: Year (2000, 2010, 2015, or 2020). Required.

    Returns:
        JSON with income distribution across various brackets
    """
    # Validate parameters
    error = _validate_population_params(planning_area, year)
    if error:
        return error

    return await _call_api(
        POP_HOUSEHOLD_INCOME, {"planningArea": planning_area, "year": year}
    )


@mcp.tool()
async def get_household_size(planning_area: str, year: int) -> str:
    """
    Get household size distribution for a planning area.

    API Reference: https://www.onemap.gov.sg/apidocs/populationquery

    Args:
        planning_area: Planning area name (e.g., "Bedok", "Tampines"). Required.
        year: Year (2000, 2010, 2015, or 2020). Required.

    Returns:
        JSON with household size counts (1-person, 2-person, etc.)
    """
    # Validate parameters
    error = _validate_population_params(planning_area, year)
    if error:
        return error

    return await _call_api(
        POP_HOUSEHOLD_SIZE, {"planningArea": planning_area, "year": year}
    )


@mcp.tool()
async def get_household_structure(planning_area: str, year: int) -> str:
    """
    Get household structure data for a planning area.

    API Reference: https://www.onemap.gov.sg/apidocs/populationquery

    Args:
        planning_area: Planning area name (e.g., "Bedok", "Tampines"). Required.
        year: Year (2000, 2010, 2015, or 2020). Required.

    Returns:
        JSON with household structure (no_family_nucleus, 1-gen, 2-gen, 3-gen, etc.)
    """
    # Validate parameters
    error = _validate_population_params(planning_area, year)
    if error:
        return error

    return await _call_api(
        POP_HOUSEHOLD_STRUCTURE, {"planningArea": planning_area, "year": year}
    )


@mcp.tool()
async def get_income_from_work(planning_area: str, year: int) -> str:
    """
    Get individual income from work data for a planning area.

    API Reference: https://www.onemap.gov.sg/apidocs/populationquery

    Args:
        planning_area: Planning area name (e.g., "Bedok", "Tampines"). Required.
        year: Year (2000, 2010, 2015, or 2020). Required.

    Returns:
        JSON with income distribution across various brackets
    """
    # Validate parameters
    error = _validate_population_params(planning_area, year)
    if error:
        return error

    return await _call_api(
        POP_INCOME_FROM_WORK, {"planningArea": planning_area, "year": year}
    )


@mcp.tool()
async def get_industry_of_population(planning_area: str, year: int) -> str:
    """
    Get industry of employment data for a planning area.

    API Reference: https://www.onemap.gov.sg/apidocs/populationquery

    Args:
        planning_area: Planning area name (e.g., "Bedok", "Tampines"). Required.
        year: Year (2000, 2010, 2015, or 2020). Required.

    Returns:
        JSON with industry distribution (manufacturing, construction, retail, etc.)
    """
    # Validate parameters
    error = _validate_population_params(planning_area, year)
    if error:
        return error

    return await _call_api(POP_INDUSTRY, {"planningArea": planning_area, "year": year})


@mcp.tool()
async def get_language_literacy(planning_area: str, year: int) -> str:
    """
    Get language literacy data for a planning area.

    API Reference: https://www.onemap.gov.sg/apidocs/populationquery

    Args:
        planning_area: Planning area name (e.g., "Bedok", "Tampines"). Required.
        year: Year (2000, 2010, 2015, or 2020). Required.

    Returns:
        JSON with literacy in various languages and combinations
    """
    # Validate parameters
    error = _validate_population_params(planning_area, year)
    if error:
        return error

    return await _call_api(
        POP_LANGUAGE_LITERATE, {"planningArea": planning_area, "year": year}
    )


@mcp.tool()
async def get_marital_status(
    planning_area: str,
    year: int,
    gender: str = None,
) -> str:
    """
    Get marital status data for a planning area.

    API Reference: https://www.onemap.gov.sg/apidocs/populationquery

    Args:
        planning_area: Planning area name (e.g., "Bedok", "Tampines"). Required.
        year: Year (2000, 2010, 2015, or 2020). Required.
        gender: Optional "male" or "female" filter

    Returns:
        JSON with marital status counts (single, married, widowed, divorced)
    """
    # Validate parameters
    error = _validate_population_params(planning_area, year, gender)
    if error:
        return error

    params: Dict[str, Any] = {"planningArea": planning_area, "year": year}
    if gender:
        params["gender"] = gender
    return await _call_api(POP_MARITAL_STATUS, params)


@mcp.tool()
async def get_mode_of_transport_school(planning_area: str, year: int) -> str:
    """
    Get mode of transport to school data for a planning area.

    API Reference: https://www.onemap.gov.sg/apidocs/populationquery

    Args:
        planning_area: Planning area name (e.g., "Bedok", "Tampines"). Required.
        year: Year (2000, 2010, 2015, or 2020). Required.

    Returns:
        JSON with transport mode distribution (bus, MRT, car, walking, etc.)
    """
    # Validate parameters
    error = _validate_population_params(planning_area, year)
    if error:
        return error

    return await _call_api(
        POP_TRANSPORT_SCHOOL, {"planningArea": planning_area, "year": year}
    )


@mcp.tool()
async def get_mode_of_transport_work(planning_area: str, year: int) -> str:
    """
    Get mode of transport to work data for a planning area.

    API Reference: https://www.onemap.gov.sg/apidocs/populationquery

    Args:
        planning_area: Planning area name (e.g., "Bedok", "Tampines"). Required.
        year: Year (2000, 2010, 2015, or 2020). Required.

    Returns:
        JSON with transport mode distribution (bus, MRT, car, motorcycle, etc.)
    """
    # Validate parameters
    error = _validate_population_params(planning_area, year)
    if error:
        return error

    return await _call_api(
        POP_TRANSPORT_WORK, {"planningArea": planning_area, "year": year}
    )


@mcp.tool()
async def get_population_age_group(
    planning_area: str,
    year: int,
    gender: str = None,
) -> str:
    """
    Get population by age group for a planning area.

    API Reference: https://www.onemap.gov.sg/apidocs/populationquery

    Args:
        planning_area: Planning area name (e.g., "Bedok", "Tampines"). Required.
        year: Year (2000, 2010, 2015, or 2020). Required.
        gender: Optional "male" or "female" filter

    Returns:
        JSON with population counts by age brackets (0-4, 5-9, ..., 85+)
    """
    # Validate parameters
    error = _validate_population_params(planning_area, year, gender)
    if error:
        return error

    params: Dict[str, Any] = {"planningArea": planning_area, "year": year}
    if gender:
        params["gender"] = gender
    return await _call_api(POP_AGE_GROUP, params)


@mcp.tool()
async def get_religion_data(planning_area: str, year: int) -> str:
    """
    Get religion distribution data for a planning area.

    API Reference: https://www.onemap.gov.sg/apidocs/populationquery

    Args:
        planning_area: Planning area name (e.g., "Bedok", "Tampines"). Required.
        year: Year (2000, 2010, 2015, or 2020). Required.

    Returns:
        JSON with religion distribution (buddhism, islam, christianity, etc.)
    """
    # Validate parameters
    error = _validate_population_params(planning_area, year)
    if error:
        return error

    return await _call_api(POP_RELIGION, {"planningArea": planning_area, "year": year})


@mcp.tool()
async def get_spoken_language_at_home(planning_area: str, year: int) -> str:
    """
    Get spoken language at home data for a planning area.

    API Reference: https://www.onemap.gov.sg/apidocs/populationquery

    Args:
        planning_area: Planning area name (e.g., "Bedok", "Tampines"). Required.
        year: Year (2000, 2010, 2015, or 2020). Required.

    Returns:
        JSON with language distribution and combinations
    """
    # Validate parameters
    error = _validate_population_params(planning_area, year)
    if error:
        return error

    return await _call_api(
        POP_SPOKEN_LANGUAGE, {"planningArea": planning_area, "year": year}
    )


@mcp.tool()
async def get_tenancy_data(planning_area: str, year: int) -> str:
    """
    Get tenancy data (owner vs tenant) for a planning area.

    API Reference: https://www.onemap.gov.sg/apidocs/populationquery

    Args:
        planning_area: Planning area name (e.g., "Bedok", "Tampines"). Required.
        year: Year (2000, 2010, 2015, or 2020). Required.

    Returns:
        JSON with tenancy distribution (owner, tenant, others)
    """
    # Validate parameters
    error = _validate_population_params(planning_area, year)
    if error:
        return error

    return await _call_api(POP_TENANCY, {"planningArea": planning_area, "year": year})


@mcp.tool()
async def get_dwelling_type_household(planning_area: str, year: int) -> str:
    """
    Get dwelling type by household for a planning area.

    API Reference: https://www.onemap.gov.sg/apidocs/populationquery

    Args:
        planning_area: Planning area name (e.g., "Bedok", "Tampines"). Required.
        year: Year (2000, 2010, 2015, or 2020). Required.

    Returns:
        JSON with dwelling types (HDB 1-5 room, condos, landed, etc.)
    """
    # Validate parameters
    error = _validate_population_params(planning_area, year)
    if error:
        return error

    return await _call_api(
        POP_DWELLING_HOUSEHOLD, {"planningArea": planning_area, "year": year}
    )


@mcp.tool()
async def get_dwelling_type_population(planning_area: str, year: int) -> str:
    """
    Get dwelling type by population count for a planning area.

    API Reference: https://www.onemap.gov.sg/apidocs/populationquery

    Args:
        planning_area: Planning area name (e.g., "Bedok", "Tampines"). Required.
        year: Year (2000, 2010, 2015, or 2020). Required.

    Returns:
        JSON with population counts by dwelling type
    """
    # Validate parameters
    error = _validate_population_params(planning_area, year)
    if error:
        return error

    return await _call_api(
        POP_DWELLING_POP, {"planningArea": planning_area, "year": year}
    )


# =============================================================================
# NEARBY TRANSPORT APIs
# =============================================================================


@mcp.tool()
async def get_nearby_mrt_stations(
    latitude: float,
    longitude: float,
    radius_in_meters: int = None,
) -> str:
    """
    Find nearby MRT and LRT stations from a given location.

    API Reference: https://www.onemap.gov.sg/apidocs/nearbytransport

    Args:
        latitude: Latitude in WGS84 format. Required.
        longitude: Longitude in WGS84 format. Required.
        radius_in_meters: Search radius (default 2000, max 5000). Must be between 1 and 5000.

    Returns:
        JSON list of nearby stations with id, name, coordinates, and road
    """
    # Validate radius_in_meters range
    if radius_in_meters is not None and (
        radius_in_meters < 1 or radius_in_meters > 5000
    ):
        return utils.format_response(
            {"success": False, "error": "radius_in_meters must be between 1 and 5000."}
        )

    params: Dict[str, Any] = {"latitude": latitude, "longitude": longitude}
    if radius_in_meters is not None:
        params["radius_in_meters"] = radius_in_meters
    return await _call_api(NEARBY_MRT, params)


@mcp.tool()
async def get_nearby_bus_stops(
    latitude: float,
    longitude: float,
    radius_in_meters: int = None,
) -> str:
    """
    Find nearby bus stops from a given location.

    API Reference: https://www.onemap.gov.sg/apidocs/nearbytransport

    Args:
        latitude: Latitude in WGS84 format. Required.
        longitude: Longitude in WGS84 format. Required.
        radius_in_meters: Search radius (default 2000, max 5000). Must be between 1 and 5000.

    Returns:
        JSON list of nearby bus stops with id, name, coordinates, and road
    """
    # Validate radius_in_meters range
    if radius_in_meters is not None and (
        radius_in_meters < 1 or radius_in_meters > 5000
    ):
        return utils.format_response(
            {"success": False, "error": "radius_in_meters must be between 1 and 5000."}
        )

    params: Dict[str, Any] = {"latitude": latitude, "longitude": longitude}
    if radius_in_meters is not None:
        params["radius_in_meters"] = radius_in_meters
    return await _call_api(NEARBY_BUS, params)


# =============================================================================
# STATIC MAP API
# =============================================================================


@mcp.tool()
async def get_static_map(
    layer_chosen: str,
    zoom: int,
    width: int,
    height: int,
    latitude: float = None,
    longitude: float = None,
    postal: str = None,
    polygons: str = None,
    lines: str = None,
    points: str = None,
    color: str = None,
    fill_color: str = None,
) -> str:
    """
    Generate a static map image in PNG format with optional overlays.

    Returns the image as base64-encoded PNG data. Users can overlay points,
    polygons, or polylines on the map.

    API Reference: https://www.onemap.gov.sg/apidocs/staticmap

    Args:
        layer_chosen: Base map style - "night", "grey", "original", "default", or "landlot". Required.
        zoom: Zoom level (11-19). Lower values = more zoomed out. Required.
        width: Image width in pixels (128-512). Required.
        height: Image height in pixels (128-512). Required.
        latitude: Latitude in WGS84 format. Either lat/lon or postal required.
        longitude: Longitude in WGS84 format. Either lat/lon or postal required.
        postal: Postal code. Either lat/lon or postal required.
        polygons: Polygon coordinates to overlay. Format:
            "[[lat1,lon1],[lat2,lon2],...,[lat1,lon1]]:R,G,B"
            Multiple polygons separated by pipe (|). Start/end points must match.
        lines: Line coordinates to overlay. Format:
            "[[lat1,lon1],[lat2,lon2]]:R,G,B:thickness"
            Multiple lines separated by pipe (|).
        points: Point coordinates to overlay. Format:
            "[lat,lon,\"R,G,B\"]|[lat,lon,\"R,G,B\"]"
            Example: "[1.31955,103.84223,\"255,255,178\"]|[1.31801,103.84224,\"175,50,0\"]"
        color: Color for all lines in RGB format (e.g., "255,0,255").
        fill_color: Fill color for all polygons in RGB format (e.g., "0,255,0").

    Returns:
        JSON with base64-encoded PNG image data and metadata
    """
    # Validate layer_chosen
    valid_layers = ["night", "grey", "original", "default", "landlot"]
    if layer_chosen not in valid_layers:
        return utils.format_response(
            {
                "success": False,
                "error": f"Invalid layer_chosen. Must be one of: {', '.join(valid_layers)}",
            }
        )

    # Validate zoom level
    if zoom < 11 or zoom > 19:
        return utils.format_response(
            {"success": False, "error": "Please enter a valid zoom level (11-19)."}
        )

    # Validate width
    if width < 128 or width > 512:
        return utils.format_response(
            {
                "success": False,
                "error": "Please enter a valid width (128-512 pixels).",
            }
        )

    # Validate height
    if height < 128 or height > 512:
        return utils.format_response(
            {
                "success": False,
                "error": "Please enter a valid height (128-512 pixels).",
            }
        )

    # Validate that either lat/lon or postal is provided
    has_coordinates = latitude is not None and longitude is not None
    has_postal = postal is not None and postal.strip() != ""
    if not has_coordinates and not has_postal:
        return utils.format_response(
            {
                "success": False,
                "error": "Please enter a pair of valid latitude & longitude, or a postal code.",
            }
        )

    params: Dict[str, Any] = {
        "layerchosen": layer_chosen,
        "zoom": zoom,
        "width": width,
        "height": height,
    }

    if latitude is not None:
        params["latitude"] = latitude
    if longitude is not None:
        params["longitude"] = longitude
    if postal is not None:
        params["postal"] = postal
    if polygons is not None:
        params["polygons"] = polygons
    if lines is not None:
        params["lines"] = lines
    if points is not None:
        params["points"] = points
    if color is not None:
        params["color"] = color
    if fill_color is not None:
        params["fillColor"] = fill_color

    try:
        access_token = await token_manager.get_access_token()
        client = await utils.get_async_client(BASE_URL, REQUEST_TIMEOUT)

        response = await client.get(
            STATIC_MAP_ENDPOINT,
            params=params,
            headers={"Authorization": access_token},
        )
        response.raise_for_status()

        # Encode the PNG image as base64
        image_base64 = base64.b64encode(response.content).decode("utf-8")

        return utils.format_response(
            utils.success_response(
                {
                    "image_base64": image_base64,
                    "content_type": response.headers.get("content-type", "image/png"),
                    "size_bytes": len(response.content),
                    "width": width,
                    "height": height,
                }
            )
        )
    except httpx.HTTPError as exc:
        return utils.format_response(utils.handle_http_error(exc))


# =============================================================================
# URA SPACE API - PROPERTY & PLANNING DATA
# =============================================================================


@mcp.tool()
async def ura_private_residential_transactions(
    batch: int = 1,
) -> str:
    """
    Get private residential property sales transactions from URA (past 5 years).
    
    Returns transaction records including sale price, area, tenure (freehold/99-year/etc),
    district, project name, and transaction date.
    
    API Reference: https://eservice.ura.gov.sg/maps/api/
    
    Args:
        batch: Batch number 1-4, split by postal districts:
               1 = districts 01-07, 2 = districts 08-14,
               3 = districts 15-21, 4 = districts 22-28
    
    Returns:
        JSON with private residential transaction records including tenure info
    """
    try:
        result = await ura_client.get_private_residential_transactions(batch)
        return utils.format_response(utils.success_response(result))
    except httpx.HTTPError as exc:
        return utils.format_response(utils.handle_http_error(exc))
    except ValueError as exc:
        return utils.format_response(utils.error_response(str(exc)))


@mcp.tool()
async def ura_private_rental_contracts(
    ref_period: str = "25q4",
) -> str:
    """
    Get private residential rental contracts from URA (past 5 years).
    
    Returns rental contract records including monthly rent, floor area,
    property type, and district information.
    
    Args:
        ref_period: Reference quarter in yyqq format (e.g., "25q1" for 2025 Q1)
    
    Returns:
        JSON with private rental contract records
    """
    try:
        result = await ura_client.get_private_rental_data(ref_period)
        return utils.format_response(utils.success_response(result))
    except httpx.HTTPError as exc:
        return utils.format_response(utils.handle_http_error(exc))
    except ValueError as exc:
        return utils.format_response(utils.error_response(str(exc)))


@mcp.tool()
async def ura_median_rentals() -> str:
    """
    Get median rentals for private non-landed residential properties from URA.
    
    Returns median rental data (past 3 years) for properties with at least
    10 rental contracts in the reference period. Includes 25th percentile,
    median, and 75th percentile PSF values.
    
    Returns:
        JSON with median rental records by project
    """
    try:
        result = await ura_client.get_median_rentals()
        return utils.format_response(utils.success_response(result))
    except httpx.HTTPError as exc:
        return utils.format_response(utils.handle_http_error(exc))
    except ValueError as exc:
        return utils.format_response(utils.error_response(str(exc)))


@mcp.tool()
async def ura_developer_sales(
    ref_period: str = "0925",
) -> str:
    """
    Get private residential units sold by developers from URA.
    
    Returns prices and sales data for completed and uncompleted private
    residential units and executive condominiums sold by developers.
    
    Args:
        ref_period: Reference month in mmyy format (e.g., "0925" for Sep 2025)
    
    Returns:
        JSON with developer sales records including median/lowest/highest prices
    """
    try:
        result = await ura_client.get_developer_sales(ref_period)
        return utils.format_response(utils.success_response(result))
    except httpx.HTTPError as exc:
        return utils.format_response(utils.handle_http_error(exc))
    except ValueError as exc:
        return utils.format_response(utils.error_response(str(exc)))


@mcp.tool()
async def ura_residential_pipeline() -> str:
    """
    Get private residential projects in the pipeline from URA.
    
    Returns information about upcoming residential projects including:
    - Project name and location
    - Number of units by type (detached, semi-detached, terrace, apartment, condo)
    - Expected TOP year
    - Developer name
    
    Returns:
        JSON with residential pipeline project records
    """
    try:
        result = await ura_client.get_residential_pipeline()
        return utils.format_response(utils.success_response(result))
    except httpx.HTTPError as exc:
        return utils.format_response(utils.handle_http_error(exc))
    except ValueError as exc:
        return utils.format_response(utils.error_response(str(exc)))


@mcp.tool()
async def ura_planning_decisions(
    year: int = 2025,
) -> str:
    """
    Get planning application decisions from URA.
    
    Returns information about Written Permission applications that have been
    granted or rejected by URA, including:
    - Submission number and decision number
    - Decision date and type
    - Site address and MK/TS lot number
    - Proposal description
    
    Args:
        year: Year to retrieve (records after 2000 only)
    
    Returns:
        JSON with planning decision records
    """
    try:
        result = await ura_client.get_planning_decisions(year)
        return utils.format_response(utils.success_response(result))
    except httpx.HTTPError as exc:
        return utils.format_response(utils.handle_http_error(exc))
    except ValueError as exc:
        return utils.format_response(utils.error_response(str(exc)))


@mcp.tool()
async def ura_car_park_availability() -> str:
    """
    Get real-time URA car park availability.
    
    Returns live availability data for URA car parks across Singapore,
    updated every 3-5 minutes. Includes:
    - Car park code
    - Lot type (Car/Motorcycle/Heavy Vehicle)
    - Available lots
    - Coordinates in SVY21 format
    
    Returns:
        JSON with car park availability records
    """
    try:
        result = await ura_client.get_car_park_availability()
        return utils.format_response(utils.success_response(result))
    except httpx.HTTPError as exc:
        return utils.format_response(utils.handle_http_error(exc))
    except ValueError as exc:
        return utils.format_response(utils.error_response(str(exc)))


@mcp.tool()
async def ura_car_park_details() -> str:
    """
    Get URA car park list and parking rates.
    
    Returns detailed information about URA short-term car parks including:
    - Car park name and code
    - Weekday, Saturday, Sunday/PH rates
    - Parking hours and rate duration
    - Parking system type (Coupon/Electronic)
    - Capacity and coordinates
    
    Returns:
        JSON with car park detail records
    """
    try:
        result = await ura_client.get_car_park_details()
        return utils.format_response(utils.success_response(result))
    except httpx.HTTPError as exc:
        return utils.format_response(utils.handle_http_error(exc))
    except ValueError as exc:
        return utils.format_response(utils.error_response(str(exc)))


# =============================================================================
# AMENITIES & ELEVATION APIs
# =============================================================================

# Common amenity theme query names
AMENITY_THEMES = {
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
    "mrt_stations": "tra_poly",
    "bus_stops": "hdb_car_park_information",
    "schools": "kindergartens",
    "heritage_trees": "heritagetrees",
    "monuments": "monuments",
    "hotels": "hotels",
}


@mcp.tool()
async def get_nearby_amenities(
    latitude: float,
    longitude: float,
    amenity_type: str,
    radius_meters: float = 1000,
) -> str:
    """
    Get amenities near a location within a specified radius.
    
    This is a convenience tool that queries OneMap themes for amenities
    within a bounding box around the specified location.
    
    Args:
        latitude: Center point latitude (WGS84)
        longitude: Center point longitude (WGS84)
        amenity_type: Type of amenity. Options: hawker_centres, kindergartens,
                     childcare, community_clubs, parks, nparks, hospitals,
                     polyclinics, libraries, sports_facilities, eldercare,
                     heritage_trees, monuments, hotels
        radius_meters: Search radius in meters (default 1000m)
    
    Returns:
        JSON with amenities found, including names, descriptions, and coordinates
    """
    # Validate amenity type
    if amenity_type not in AMENITY_THEMES:
        return utils.format_response({
            "success": False,
            "error": f"Invalid amenity_type. Valid options: {list(AMENITY_THEMES.keys())}"
        })
    
    # Calculate bounding box (approximate degrees per meter at Singapore's latitude)
    # At ~1.3°N: 1 degree latitude ≈ 111km, 1 degree longitude ≈ 111km * cos(1.3°) ≈ 110.9km
    lat_delta = radius_meters / 111000
    lon_delta = radius_meters / 110900
    
    extents = f"{latitude - lat_delta},{longitude - lon_delta},{latitude + lat_delta},{longitude + lon_delta}"
    query_name = AMENITY_THEMES[amenity_type]
    
    params: Dict[str, Any] = {"queryName": query_name, "extents": extents}
    
    try:
        result = await _call_api(THEME_RETRIEVE, params)
        # Parse the result to add distance information
        import json as json_lib
        data = json_lib.loads(result) if isinstance(result, str) else result
        
        if "SrchResults" in data and len(data["SrchResults"]) > 1:
            # Calculate distance to each result
            import math
            for item in data["SrchResults"][1:]:  # Skip first item (metadata)
                if "LatLng" in item:
                    try:
                        coords = item["LatLng"]
                        # Parse coordinates - format varies
                        if isinstance(coords, str) and coords.startswith("[["):
                            # Polygon format
                            pass
                        elif isinstance(coords, str):
                            # Point format "lon,lat" or similar
                            parts = coords.replace("[", "").replace("]", "").split(",")
                            if len(parts) >= 2:
                                item_lon = float(parts[0])
                                item_lat = float(parts[1])
                                # Haversine distance
                                R = 6371000  # Earth radius in meters
                                dlat = math.radians(item_lat - latitude)
                                dlon = math.radians(item_lon - longitude)
                                a = math.sin(dlat/2)**2 + math.cos(math.radians(latitude)) * math.cos(math.radians(item_lat)) * math.sin(dlon/2)**2
                                c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
                                item["distance_meters"] = round(R * c)
                    except:
                        pass
        
        return utils.format_response(data)
    except httpx.HTTPError as exc:
        return utils.format_response(utils.handle_http_error(exc))


@mcp.tool()
async def get_elevation(latitude: float, longitude: float) -> str:
    """
    Get terrain elevation at a specific coordinate.
    
    Uses the Open-Elevation API to get terrain height above sea level.
    This is useful for 3D mapping and terrain analysis in Singapore.
    
    Note: This uses global SRTM data (30m resolution). For higher precision
    Singapore-specific elevation data, consider SLA GeoSpace (requires subscription).
    
    Args:
        latitude: Latitude in WGS84 (e.g., 1.3521)
        longitude: Longitude in WGS84 (e.g., 103.8198)
    
    Returns:
        JSON with elevation in meters above sea level
    """
    try:
        # Use standalone client for external API
        async with httpx.AsyncClient() as client:
            # Use Open-Elevation API (free, no key required)
            url = f"{ELEVATION_API_URL}?locations={latitude},{longitude}"
        
            response = await client.get(url, timeout=10.0)
            response.raise_for_status()
            
            data = response.json()
            
            if "results" in data and len(data["results"]) > 0:
                elevation = data["results"][0].get("elevation")
                return utils.format_response({
                    "success": True,
                    "latitude": latitude,
                    "longitude": longitude,
                    "elevation_meters": elevation,
                    "data_source": "Open-Elevation (SRTM 30m)",
                })
            else:
                return utils.format_response({
                    "success": False,
                    "error": "No elevation data available for this location"
                })
            
    except httpx.TimeoutException:
        return utils.format_response({
            "success": False,
            "error": "Elevation service timed out. Try again later."
        })
    except httpx.HTTPError as exc:
        return utils.format_response(utils.handle_http_error(exc))


@mcp.tool()
async def get_elevation_profile(coordinates: str) -> str:
    """
    Get elevation profile for multiple points along a path.
    
    Useful for analyzing terrain along a route or transect.
    
    Args:
        coordinates: Pipe-separated lat,lon pairs
                    (e.g., "1.35,103.82|1.36,103.83|1.37,103.84")
    
    Returns:
        JSON with elevation for each point
    """
    try:
        # Parse coordinates
        points = []
        for pair in coordinates.split("|"):
            lat, lon = pair.strip().split(",")
            points.append({"latitude": float(lat), "longitude": float(lon)})
        
        if len(points) < 2:
            return utils.format_response({
                "success": False,
                "error": "At least 2 coordinate pairs required for elevation profile"
            })
        
        if len(points) > 100:
            return utils.format_response({
                "success": False,
                "error": "Maximum 100 points allowed per request"
            })
        
        # Use standalone client for external API
        async with httpx.AsyncClient() as client:
            # Build request for Open-Elevation API
            locations = "|".join([f"{p['latitude']},{p['longitude']}" for p in points])
            url = f"{ELEVATION_API_URL}?locations={locations}"
            
            response = await client.get(url, timeout=30.0)
            response.raise_for_status()
            
            data = response.json()
            
            if "results" in data:
                profile = []
                for i, result in enumerate(data["results"]):
                    profile.append({
                        "point_index": i,
                        "latitude": result.get("latitude"),
                        "longitude": result.get("longitude"),
                        "elevation_meters": result.get("elevation"),
                    })
                
                # Calculate stats
                elevations = [p["elevation_meters"] for p in profile if p["elevation_meters"] is not None]
                
                return utils.format_response({
                    "success": True,
                    "profile": profile,
                    "statistics": {
                        "min_elevation": min(elevations) if elevations else None,
                        "max_elevation": max(elevations) if elevations else None,
                        "elevation_range": max(elevations) - min(elevations) if elevations else None,
                        "point_count": len(profile),
                    },
                    "data_source": "Open-Elevation (SRTM 30m)",
                })
            else:
                return utils.format_response({
                    "success": False,
                    "error": "No elevation data available"
                })
            
    except ValueError as exc:
        return utils.format_response({
            "success": False,
            "error": f"Invalid coordinates format: {exc}"
        })
    except httpx.TimeoutException:
        return utils.format_response({
            "success": False,
            "error": "Elevation service timed out. Try again later."
        })
    except httpx.HTTPError as exc:
        return utils.format_response(utils.handle_http_error(exc))


# =============================================================================
# SERVER ENTRY POINT
# =============================================================================

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="OneMap MCP Server")
    parser.add_argument(
        "--transport",
        choices=["stdio", "streamable-http"],
        default="stdio",
        help="Transport mode: 'stdio' for local/CLI, 'streamable-http' for HTTP/AI Foundry"
    )
    parser.add_argument(
        "--host",
        default="0.0.0.0",
        help="Host to bind to (streamable-http mode only)"
    )
    parser.add_argument(
        "--port",
        type=int,
        default=8000,
        help="Port to listen on (streamable-http mode only)"
    )
    args = parser.parse_args()
    
    if args.transport == "streamable-http":
        # Run with Streamable HTTP transport for AI Foundry / HTTP clients
        # This is the recommended transport for production deployments
        import uvicorn
        
        # Get the FastMCP streamable HTTP app (transport_security already disabled in FastMCP init)
        app = mcp.streamable_http_app()
        
        # Run with uvicorn
        uvicorn.run(app, host=args.host, port=args.port)
    else:
        # Run with stdio transport for local testing / Claude Desktop
        mcp.run()


