from datetime import date

from fastapi import FastAPI, HTTPException, Query
from workers import asgi

from calculator import calculate_holidays
from loader import (
    DataError,
    get_country_codes,
    get_subdivision,
    load_country,
)


app = FastAPI(
    title="Holidays API",
    description="Free public and bank holiday data API.",
    version="1.0.0",
)


def validate_country(country: str) -> str:
    country = country.strip().upper()

    if len(country) != 2 or not country.isalpha():
        raise HTTPException(
            status_code=400,
            detail="Country must be a two-letter ISO 3166-1 code.",
        )

    return country


def validate_year(year: int) -> int:
    if year < 1000 or year > 9999:
        raise HTTPException(
            status_code=400,
            detail="Year must be a four-digit year.",
        )

    return year


def get_data(country: str) -> dict:
    try:
        return load_country(country)
    except DataError as exc:
        raise HTTPException(
            status_code=404,
            detail=str(exc),
        ) from exc


@app.get("/")
async def root():
    return {
        "name": "Holidays API",
        "version": app.version,
        "status": "online",
    }


@app.get("/api/v1")
async def api_info():
    return {
        "version": "1",
        "endpoints": {
            "list": "/api/v1/list",
            "today": "/api/v1/today",
            "countries": "/api/v1/countries",
        },
    }


@app.get("/api/v1/countries")
async def countries():
    return {
        "countries": get_country_codes()
    }


@app.get("/api/v1/list")
async def list_holidays(
    country: str,
    year: int,
    subdivision: str | None = Query(default=None),
):
    country = validate_country(country)
    year = validate_year(year)

    country_data = get_data(country)

    if subdivision:
        subdivision = subdivision.strip().upper()

        if get_subdivision(
            country_data,
            subdivision
        ) is None:
            raise HTTPException(
                status_code=404,
                detail=(
                    f"Subdivision '{subdivision}' "
                    f"is not supported for {country}."
                ),
            )

    try:
        holidays = calculate_holidays(
            country_data,
            year,
            subdivision,
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=500,
            detail=str(exc),
        ) from exc

    return {
        "country": country,
        "year": year,
        "subdivision": subdivision,
        "holidays": [
            holiday.to_dict()
            for holiday in holidays
        ],
    }


@app.get("/api/v1/today")
async def today(country: str):
    country = validate_country(country)

    country_data = get_data(country)
    current_date = date.today()

    try:
        holidays = calculate_holidays(
            country_data,
            current_date.year,
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=500,
            detail=str(exc),
        ) from exc

    matches = [
        holiday.to_dict()
        for holiday in holidays
        if holiday.date == current_date
    ]

    return {
        "country": country,
        "date": current_date.isoformat(),
        "holiday": matches[0] if matches else None,
    }


Default = asgi.entrypoint(app)