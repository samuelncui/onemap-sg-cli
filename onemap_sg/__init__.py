"""
onemap-sg — Python library for Singapore OneMap APIs.

Usage::

    import asyncio
    import onemap_sg

    result = asyncio.run(onemap_sg.search("Orchard Road"))
    print(result["results"][0]["ADDRESS"])
"""

from onemap_sg.search import search
from onemap_sg.geocode import reverse_geocode_wgs84, reverse_geocode_svy21
from onemap_sg.routing import route_walk_drive_cycle, route_public_transport
from onemap_sg.coordinate import (
    convert_4326_to_3857,
    convert_4326_to_3414,
    convert_3414_to_3857,
    convert_3414_to_4326,
    convert_3857_to_3414,
    convert_3857_to_4326,
)
from onemap_sg.themes import (
    get_all_themes_info,
    get_theme_info,
    check_theme_status,
    retrieve_theme,
)
from onemap_sg.planning_area import (
    get_all_planning_areas,
    get_planning_area_names,
    get_planning_area_by_location,
)
from onemap_sg.population import (
    get_population_age_group,
    get_economic_status,
    get_education_status,
    get_ethnic_distribution,
    get_household_monthly_income,
    get_household_size,
    get_household_structure,
    get_income_from_work,
    get_industry_of_population,
    get_language_literacy,
    get_marital_status,
    get_mode_of_transport_school,
    get_mode_of_transport_work,
    get_religion_data,
    get_spoken_language_at_home,
    get_tenancy_data,
    get_dwelling_type_household,
    get_dwelling_type_population,
)
from onemap_sg.transport import get_nearby_mrt_stations, get_nearby_bus_stops
from onemap_sg.static_map import get_static_map
from onemap_sg.elevation import get_elevation, get_elevation_profile
from onemap_sg.amenities import get_nearby_amenities
from onemap_sg.ura import (
    get_private_residential_transactions,
    get_private_rental_contracts,
    get_median_rentals,
    get_developer_sales,
    get_residential_pipeline,
    get_planning_decisions,
    get_car_park_availability,
    get_car_park_details,
)

__all__ = [
    # Search & Geocode
    "search",
    "reverse_geocode_wgs84",
    "reverse_geocode_svy21",
    # Routing
    "route_walk_drive_cycle",
    "route_public_transport",
    # Coordinate Converters
    "convert_4326_to_3857",
    "convert_4326_to_3414",
    "convert_3414_to_3857",
    "convert_3414_to_4326",
    "convert_3857_to_3414",
    "convert_3857_to_4326",
    # Themes
    "get_all_themes_info",
    "get_theme_info",
    "check_theme_status",
    "retrieve_theme",
    # Planning Area
    "get_all_planning_areas",
    "get_planning_area_names",
    "get_planning_area_by_location",
    # Population
    "get_population_age_group",
    "get_economic_status",
    "get_education_status",
    "get_ethnic_distribution",
    "get_household_monthly_income",
    "get_household_size",
    "get_household_structure",
    "get_income_from_work",
    "get_industry_of_population",
    "get_language_literacy",
    "get_marital_status",
    "get_mode_of_transport_school",
    "get_mode_of_transport_work",
    "get_religion_data",
    "get_spoken_language_at_home",
    "get_tenancy_data",
    "get_dwelling_type_household",
    "get_dwelling_type_population",
    # Transport
    "get_nearby_mrt_stations",
    "get_nearby_bus_stops",
    # Static Map
    "get_static_map",
    # Elevation
    "get_elevation",
    "get_elevation_profile",
    # Amenities
    "get_nearby_amenities",
    # URA
    "get_private_residential_transactions",
    "get_private_rental_contracts",
    "get_median_rentals",
    "get_developer_sales",
    "get_residential_pipeline",
    "get_planning_decisions",
    "get_car_park_availability",
    "get_car_park_details",
]
