"""
OneMap population query API — demographics and statistics by planning area.

Provides population data from the Singapore Census including age groups,
economic status, education, ethnicity, income, household data, language,
marital status, religion, transport modes, dwelling types, and more.
"""

from __future__ import annotations

from typing import Any

from onemap_sg._client import (
    _call_api,
    POP_AGE_GROUP,
    POP_DWELLING_HOUSEHOLD,
    POP_DWELLING_POP,
    POP_ECONOMIC_STATUS,
    POP_EDUCATION,
    POP_ETHNIC_GROUP,
    POP_HOUSEHOLD_INCOME,
    POP_HOUSEHOLD_SIZE,
    POP_HOUSEHOLD_STRUCTURE,
    POP_INCOME_FROM_WORK,
    POP_INDUSTRY,
    POP_LANGUAGE_LITERATE,
    POP_MARITAL_STATUS,
    POP_RELIGION,
    POP_SPOKEN_LANGUAGE,
    POP_TENANCY,
    POP_TRANSPORT_SCHOOL,
    POP_TRANSPORT_WORK,
)

VALID_POPULATION_YEARS = [2000, 2010, 2015, 2020]


def _validate_population_params(
    planning_area: str, year: int, gender: str | None = None
) -> None:
    """Validate common population query parameters.  Raises ValueError on failure."""
    if not planning_area or not planning_area.strip():
        raise ValueError("Please enter planning area.")
    if year not in VALID_POPULATION_YEARS:
        raise ValueError(
            f"Please enter valid year. Valid years are: {VALID_POPULATION_YEARS}"
        )
    if gender is not None and gender.lower() not in ("male", "female"):
        raise ValueError("Your gender must be either male or female.")


async def get_population_age_group(
    planning_area: str,
    year: int,
    gender: str | None = None,
) -> dict[str, Any]:
    """Get population by age group for a planning area.

    API Reference: https://www.onemap.gov.sg/apidocs/populationquery

    Args:
        planning_area: Planning area name (e.g., "Bedok", "Tampines").
            Required.
        year: Year (2000, 2010, 2015, or 2020). Required.
        gender: Optional "male" or "female" filter.

    Returns:
        JSON dict with population counts by age brackets (0-4, 5-9, ..., 85+).

    Raises:
        ValueError: If any parameter validation fails.
    """
    _validate_population_params(planning_area, year, gender)

    params: dict[str, Any] = {"planningArea": planning_area, "year": year}
    if gender:
        params["gender"] = gender
    return await _call_api(POP_AGE_GROUP, params)


async def get_economic_status(
    planning_area: str,
    year: int,
    gender: str | None = None,
) -> dict[str, Any]:
    """Get economic status data (employed, unemployed, inactive) for a
    planning area.

    API Reference: https://www.onemap.gov.sg/apidocs/populationquery

    Args:
        planning_area: Planning area name (e.g., "Bedok", "Tampines").
            Required.
        year: Year (2000, 2010, 2015, or 2020). Required.
        gender: Optional "male" or "female" filter.

    Returns:
        JSON dict with employment statistics.

    Raises:
        ValueError: If any parameter validation fails.
    """
    _validate_population_params(planning_area, year, gender)

    params: dict[str, Any] = {"planningArea": planning_area, "year": year}
    if gender:
        params["gender"] = gender
    return await _call_api(POP_ECONOMIC_STATUS, params)


async def get_education_status(
    planning_area: str, year: int
) -> dict[str, Any]:
    """Get education attending data for a planning area.

    API Reference: https://www.onemap.gov.sg/apidocs/populationquery

    Args:
        planning_area: Planning area name (e.g., "Bedok", "Tampines").
            Required.
        year: Year (2000, 2010, 2015, or 2020). Required.

    Returns:
        JSON dict with education level statistics (pre_primary, primary,
        secondary, etc.).

    Raises:
        ValueError: If any parameter validation fails.
    """
    _validate_population_params(planning_area, year)

    return await _call_api(
        POP_EDUCATION, {"planningArea": planning_area, "year": year}
    )


async def get_ethnic_distribution(
    planning_area: str,
    year: int,
    gender: str | None = None,
) -> dict[str, Any]:
    """Get ethnic group distribution for a planning area.

    API Reference: https://www.onemap.gov.sg/apidocs/populationquery

    Args:
        planning_area: Planning area name (e.g., "Bedok", "Tampines").
            Required.
        year: Year (2000, 2010, 2015, or 2020). Required.
        gender: Optional "male" or "female" filter.

    Returns:
        JSON dict with ethnic distribution (chinese, malays, indian, others).

    Raises:
        ValueError: If any parameter validation fails.
    """
    _validate_population_params(planning_area, year, gender)

    params: dict[str, Any] = {"planningArea": planning_area, "year": year}
    if gender:
        params["gender"] = gender
    return await _call_api(POP_ETHNIC_GROUP, params)


async def get_household_monthly_income(
    planning_area: str, year: int
) -> dict[str, Any]:
    """Get monthly household income from work for a planning area.

    API Reference: https://www.onemap.gov.sg/apidocs/populationquery

    Args:
        planning_area: Planning area name (e.g., "Bedok", "Tampines").
            Required.
        year: Year (2000, 2010, 2015, or 2020). Required.

    Returns:
        JSON dict with income distribution across various brackets.

    Raises:
        ValueError: If any parameter validation fails.
    """
    _validate_population_params(planning_area, year)

    return await _call_api(
        POP_HOUSEHOLD_INCOME, {"planningArea": planning_area, "year": year}
    )


async def get_household_size(
    planning_area: str, year: int
) -> dict[str, Any]:
    """Get household size distribution for a planning area.

    API Reference: https://www.onemap.gov.sg/apidocs/populationquery

    Args:
        planning_area: Planning area name (e.g., "Bedok", "Tampines").
            Required.
        year: Year (2000, 2010, 2015, or 2020). Required.

    Returns:
        JSON dict with household size counts (1-person, 2-person, etc.).

    Raises:
        ValueError: If any parameter validation fails.
    """
    _validate_population_params(planning_area, year)

    return await _call_api(
        POP_HOUSEHOLD_SIZE, {"planningArea": planning_area, "year": year}
    )


async def get_household_structure(
    planning_area: str, year: int
) -> dict[str, Any]:
    """Get household structure data for a planning area.

    API Reference: https://www.onemap.gov.sg/apidocs/populationquery

    Args:
        planning_area: Planning area name (e.g., "Bedok", "Tampines").
            Required.
        year: Year (2000, 2010, 2015, or 2020). Required.

    Returns:
        JSON dict with household structure (no_family_nucleus, 1-gen, 2-gen,
        3-gen, etc.).

    Raises:
        ValueError: If any parameter validation fails.
    """
    _validate_population_params(planning_area, year)

    return await _call_api(
        POP_HOUSEHOLD_STRUCTURE, {"planningArea": planning_area, "year": year}
    )


async def get_income_from_work(
    planning_area: str, year: int
) -> dict[str, Any]:
    """Get individual income from work data for a planning area.

    API Reference: https://www.onemap.gov.sg/apidocs/populationquery

    Args:
        planning_area: Planning area name (e.g., "Bedok", "Tampines").
            Required.
        year: Year (2000, 2010, 2015, or 2020). Required.

    Returns:
        JSON dict with income distribution across various brackets.

    Raises:
        ValueError: If any parameter validation fails.
    """
    _validate_population_params(planning_area, year)

    return await _call_api(
        POP_INCOME_FROM_WORK, {"planningArea": planning_area, "year": year}
    )


async def get_industry_of_population(
    planning_area: str, year: int
) -> dict[str, Any]:
    """Get industry of employment data for a planning area.

    API Reference: https://www.onemap.gov.sg/apidocs/populationquery

    Args:
        planning_area: Planning area name (e.g., "Bedok", "Tampines").
            Required.
        year: Year (2000, 2010, 2015, or 2020). Required.

    Returns:
        JSON dict with industry distribution (manufacturing, construction,
        retail, etc.).

    Raises:
        ValueError: If any parameter validation fails.
    """
    _validate_population_params(planning_area, year)

    return await _call_api(
        POP_INDUSTRY, {"planningArea": planning_area, "year": year}
    )


async def get_language_literacy(
    planning_area: str, year: int
) -> dict[str, Any]:
    """Get language literacy data for a planning area.

    API Reference: https://www.onemap.gov.sg/apidocs/populationquery

    Args:
        planning_area: Planning area name (e.g., "Bedok", "Tampines").
            Required.
        year: Year (2000, 2010, 2015, or 2020). Required.

    Returns:
        JSON dict with literacy in various languages and combinations.

    Raises:
        ValueError: If any parameter validation fails.
    """
    _validate_population_params(planning_area, year)

    return await _call_api(
        POP_LANGUAGE_LITERATE, {"planningArea": planning_area, "year": year}
    )


async def get_marital_status(
    planning_area: str,
    year: int,
    gender: str | None = None,
) -> dict[str, Any]:
    """Get marital status data for a planning area.

    API Reference: https://www.onemap.gov.sg/apidocs/populationquery

    Args:
        planning_area: Planning area name (e.g., "Bedok", "Tampines").
            Required.
        year: Year (2000, 2010, 2015, or 2020). Required.
        gender: Optional "male" or "female" filter.

    Returns:
        JSON dict with marital status counts (single, married, widowed,
        divorced).

    Raises:
        ValueError: If any parameter validation fails.
    """
    _validate_population_params(planning_area, year, gender)

    params: dict[str, Any] = {"planningArea": planning_area, "year": year}
    if gender:
        params["gender"] = gender
    return await _call_api(POP_MARITAL_STATUS, params)


async def get_mode_of_transport_school(
    planning_area: str, year: int
) -> dict[str, Any]:
    """Get mode of transport to school data for a planning area.

    API Reference: https://www.onemap.gov.sg/apidocs/populationquery

    Args:
        planning_area: Planning area name (e.g., "Bedok", "Tampines").
            Required.
        year: Year (2000, 2010, 2015, or 2020). Required.

    Returns:
        JSON dict with transport mode distribution (bus, MRT, car, walking,
        etc.).

    Raises:
        ValueError: If any parameter validation fails.
    """
    _validate_population_params(planning_area, year)

    return await _call_api(
        POP_TRANSPORT_SCHOOL, {"planningArea": planning_area, "year": year}
    )


async def get_mode_of_transport_work(
    planning_area: str, year: int
) -> dict[str, Any]:
    """Get mode of transport to work data for a planning area.

    API Reference: https://www.onemap.gov.sg/apidocs/populationquery

    Args:
        planning_area: Planning area name (e.g., "Bedok", "Tampines").
            Required.
        year: Year (2000, 2010, 2015, or 2020). Required.

    Returns:
        JSON dict with transport mode distribution (bus, MRT, car, motorcycle,
        etc.).

    Raises:
        ValueError: If any parameter validation fails.
    """
    _validate_population_params(planning_area, year)

    return await _call_api(
        POP_TRANSPORT_WORK, {"planningArea": planning_area, "year": year}
    )


async def get_religion_data(
    planning_area: str, year: int
) -> dict[str, Any]:
    """Get religion distribution data for a planning area.

    API Reference: https://www.onemap.gov.sg/apidocs/populationquery

    Args:
        planning_area: Planning area name (e.g., "Bedok", "Tampines").
            Required.
        year: Year (2000, 2010, 2015, or 2020). Required.

    Returns:
        JSON dict with religion distribution (buddhism, islam, christianity,
        etc.).

    Raises:
        ValueError: If any parameter validation fails.
    """
    _validate_population_params(planning_area, year)

    return await _call_api(
        POP_RELIGION, {"planningArea": planning_area, "year": year}
    )


async def get_spoken_language_at_home(
    planning_area: str, year: int
) -> dict[str, Any]:
    """Get spoken language at home data for a planning area.

    API Reference: https://www.onemap.gov.sg/apidocs/populationquery

    Args:
        planning_area: Planning area name (e.g., "Bedok", "Tampines").
            Required.
        year: Year (2000, 2010, 2015, or 2020). Required.

    Returns:
        JSON dict with language distribution and combinations.

    Raises:
        ValueError: If any parameter validation fails.
    """
    _validate_population_params(planning_area, year)

    return await _call_api(
        POP_SPOKEN_LANGUAGE, {"planningArea": planning_area, "year": year}
    )


async def get_tenancy_data(
    planning_area: str, year: int
) -> dict[str, Any]:
    """Get tenancy data (owner vs tenant) for a planning area.

    API Reference: https://www.onemap.gov.sg/apidocs/populationquery

    Args:
        planning_area: Planning area name (e.g., "Bedok", "Tampines").
            Required.
        year: Year (2000, 2010, 2015, or 2020). Required.

    Returns:
        JSON dict with tenancy distribution (owner, tenant, others).

    Raises:
        ValueError: If any parameter validation fails.
    """
    _validate_population_params(planning_area, year)

    return await _call_api(
        POP_TENANCY, {"planningArea": planning_area, "year": year}
    )


async def get_dwelling_type_household(
    planning_area: str, year: int
) -> dict[str, Any]:
    """Get dwelling type by household for a planning area.

    API Reference: https://www.onemap.gov.sg/apidocs/populationquery

    Args:
        planning_area: Planning area name (e.g., "Bedok", "Tampines").
            Required.
        year: Year (2000, 2010, 2015, or 2020). Required.

    Returns:
        JSON dict with dwelling types (HDB 1-5 room, condos, landed, etc.).

    Raises:
        ValueError: If any parameter validation fails.
    """
    _validate_population_params(planning_area, year)

    return await _call_api(
        POP_DWELLING_HOUSEHOLD, {"planningArea": planning_area, "year": year}
    )


async def get_dwelling_type_population(
    planning_area: str, year: int
) -> dict[str, Any]:
    """Get dwelling type by population count for a planning area.

    API Reference: https://www.onemap.gov.sg/apidocs/populationquery

    Args:
        planning_area: Planning area name (e.g., "Bedok", "Tampines").
            Required.
        year: Year (2000, 2010, 2015, or 2020). Required.

    Returns:
        JSON dict with population counts by dwelling type.

    Raises:
        ValueError: If any parameter validation fails.
    """
    _validate_population_params(planning_area, year)

    return await _call_api(
        POP_DWELLING_POP, {"planningArea": planning_area, "year": year}
    )
