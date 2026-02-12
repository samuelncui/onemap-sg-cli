"""
URA Space API Client for OneMap MCP Server.
Provides access to URA's land sales, master plan, and property transaction data.

API Documentation: https://eservice.ura.gov.sg/maps/api/
"""

import os
from typing import Any, Dict, Optional
from datetime import datetime, timedelta

import httpx
import utils

# URA API Configuration
URA_BASE_URL = os.getenv("URA_BASE_URL", "https://eservice.ura.gov.sg/uraDataService")
URA_REQUEST_TIMEOUT = 30.0

# Default headers to avoid bot detection
URA_DEFAULT_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "application/json",
    "Accept-Language": "en-US,en;q=0.9",
}

# URA API Endpoints (v1 API)
URA_ENDPOINTS = {
    # Property Market Information
    "private_residential_transaction": "PMI_Resi_Transaction",
    "private_residential_rental": "PMI_Resi_Rental",
    "private_residential_median_rental": "PMI_Resi_Rental_Median",
    "private_residential_developer_sales": "PMI_Resi_Developer_Sales",
    "private_residential_pipeline": "PMI_Resi_Pipeline",
    
    # Planning Information
    "planning_decisions": "Planning_Decision",
    "approved_residential_use": "EAU_Appr_Resi_Use",
    
    # Car Park Information
    "car_park_availability": "Car_Park_Availability",
    "car_park_details": "Car_Park_Details",
    "season_car_park_details": "Season_Car_Park_Details",
}


class URATokenManager:
    """Manages URA daily token lifecycle."""
    
    def __init__(self):
        self._daily_token: Optional[str] = None
        self._token_date: Optional[datetime] = None
    
    def _is_token_valid(self) -> bool:
        """Check if the daily token is still valid (same day)."""
        if self._daily_token is None or self._token_date is None:
            return False
        # URA tokens are valid for the day they're generated
        return self._token_date.date() == datetime.now().date()
    
    async def get_daily_token(self, access_key: str) -> str:
        """
        Get a valid daily token, refreshing if necessary.
        
        URA API requires a daily token obtained using the access key.
        The token is valid for the entire day.
        """
        if self._is_token_valid():
            return self._daily_token
        
        client = await utils.get_async_client(URA_BASE_URL, URA_REQUEST_TIMEOUT)
        
        headers = {**URA_DEFAULT_HEADERS, "AccessKey": access_key}
        
        response = await client.get(
            "/insertNewToken/v1",
            headers=headers
        )
        response.raise_for_status()
        
        data = response.json()
        if data.get("Status") == "Success":
            self._daily_token = data.get("Result")
            self._token_date = datetime.now()
            return self._daily_token
        else:
            raise ValueError(f"Failed to get URA token: {data}")


# Global token manager
_ura_token_manager = URATokenManager()


def get_ura_access_key() -> str:
    """Get URA access key from environment."""
    access_key = os.getenv("URA_ACCESS_KEY")
    if not access_key:
        raise ValueError(
            "URA_ACCESS_KEY not configured. "
            "Get your access key at https://www.ura.gov.sg/maps/api/"
        )
    return access_key


async def call_ura_api(
    service: str,
    params: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """
    Make an authenticated API call to URA Data Service.
    
    Args:
        service: The URA service name (from URA_ENDPOINTS)
        params: Optional query parameters
        
    Returns:
        API response as dictionary
    """
    access_key = get_ura_access_key()
    daily_token = await _ura_token_manager.get_daily_token(access_key)
    
    client = await utils.get_async_client(URA_BASE_URL, URA_REQUEST_TIMEOUT)
    
    headers = {
        **URA_DEFAULT_HEADERS,
        "AccessKey": access_key,
        "Token": daily_token,
    }
    
    # Build the endpoint URL with all params in URL (v1 API)
    # URA API expects params in URL, not as separate query params
    endpoint = f"/invokeUraDS/v1?service={service}"
    if params:
        for key, value in params.items():
            endpoint += f"&{key}={value}"
    
    response = await client.get(
        endpoint,
        headers=headers,
    )
    response.raise_for_status()
    
    # Handle encoding issues - URA API sometimes returns non-UTF8 data
    try:
        return response.json()
    except Exception:
        # Try to decode with latin-1 as fallback
        content = response.content.decode('latin-1')
        import json
        return json.loads(content)


# =============================================================================
# HIGH-LEVEL API FUNCTIONS
# =============================================================================

async def get_private_residential_transactions(
    batch: int = 1,
) -> Dict[str, Any]:
    """
    Get private residential property transactions (past 5 years).
    
    Args:
        batch: Batch number (1-4), split by postal districts:
               1 = districts 01-07, 2 = districts 08-14, etc.
        
    Returns:
        Transaction records with price, area, tenure, district info
    """
    return await call_ura_api(
        URA_ENDPOINTS["private_residential_transaction"],
        {"batch": str(batch)}
    )


async def get_private_rental_data(
    ref_period: str = "24q4",
) -> Dict[str, Any]:
    """
    Get private residential rental contracts (past 5 years).
    
    Args:
        ref_period: Reference quarter in yyqq format (e.g., "24q1" for 2024 Q1)
        
    Returns:
        Rental contract records with rent, area, property type
    """
    return await call_ura_api(
        URA_ENDPOINTS["private_residential_rental"],
        {"refPeriod": ref_period}
    )


async def get_median_rentals() -> Dict[str, Any]:
    """
    Get median rentals for private non-landed residential properties (past 3 years).
    
    Returns:
        Median rental records by project with psf25, median, psf75
    """
    return await call_ura_api(URA_ENDPOINTS["private_residential_median_rental"])


async def get_developer_sales(
    ref_period: str = "0924",
) -> Dict[str, Any]:
    """
    Get private residential units sold by developers (past 3 years).
    
    Args:
        ref_period: Reference month in mmyy format (e.g., "0924" for Sep 2024)
        
    Returns:
        Developer sales records with prices, units available/sold
    """
    return await call_ura_api(
        URA_ENDPOINTS["private_residential_developer_sales"],
        {"refPeriod": ref_period}
    )


async def get_residential_pipeline() -> Dict[str, Any]:
    """
    Get private residential projects in the pipeline.
    
    Returns:
        Pipeline projects with unit counts by type, expected TOP year
    """
    return await call_ura_api(URA_ENDPOINTS["private_residential_pipeline"])


async def get_planning_decisions(
    year: int = 2025,
) -> Dict[str, Any]:
    """
    Get planning decisions (Written Permission granted/rejected by URA).
    
    Args:
        year: Year to retrieve (records after 2000 only)
        
    Returns:
        Planning decision records with submission details, decision type
    """
    return await call_ura_api(
        URA_ENDPOINTS["planning_decisions"],
        {"year": str(year)}
    )


async def get_car_park_availability() -> Dict[str, Any]:
    """
    Get real-time car park availability (updates every 3-5 mins).
    
    Returns:
        Car park lots availability with coordinates in SVY21 format
    """
    return await call_ura_api(URA_ENDPOINTS["car_park_availability"])


async def get_car_park_details() -> Dict[str, Any]:
    """
    Get URA car park list and rates.
    
    Returns:
        Car park details with rates, parking hours, capacity
    """
    return await call_ura_api(URA_ENDPOINTS["car_park_details"])
