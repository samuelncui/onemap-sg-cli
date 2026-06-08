"""
OneMap API configuration — constants, endpoints, environment.
"""

from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv

# Load ~/.onemap.env first, then CWD .env (CWD overrides)
_onemap_env = Path.home() / ".onemap.env"
if _onemap_env.exists():
    load_dotenv(_onemap_env)
load_dotenv()

# ---------------------------------------------------------------------------
# General
# ---------------------------------------------------------------------------

TOKEN_REFRESH_BUFFER_SECONDS = 60

BASE_URL = os.getenv("ONEMAP_BASE_URL", "https://www.onemap.gov.sg")
ELEVATION_API_URL = os.getenv(
    "ELEVATION_API_URL", "https://api.open-elevation.com/api/v1/lookup"
)

REQUEST_TIMEOUT = 30.0
JSON_HEADERS = {"Content-Type": "application/json"}

# ---------------------------------------------------------------------------
# API Endpoints
# ---------------------------------------------------------------------------

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
