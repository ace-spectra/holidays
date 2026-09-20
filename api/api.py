from datetime import date

from fastapi import FastAPI, HTTPException
from workers import asgi

app = FastAPI(
    title="Holidays API",
    description="Free public and bank holiday data API.",
    version="1.0.0",
)


@app.get("/api/v1")
async def api_info():
    return {
        "version": "1",
        "endpoints": {
            "list": "/api/v1/list",
            "today": "/api/v1/today",
        },
    }


def validate_country(country: str) -> str:
    country = country.strip().upper()

    if len(country) != 2:
        raise HTTPException(
            status_code=400,
            detail="Country must be a two-letter ISO 3166-1 code.",
        )

    if not country.isalpha():
        raise HTTPException(
            status_code=400,
            detail="Country must contain letters only.",
        )

    return country


def validate_year(year: int) -> int:
    if year < 1000 or year > 9999:
        raise HTTPException(
            status_code=400,
            detail="Year must be a four-digit year (e.g. 2026).",
        )

    return year


@app.get("/api/v1/list")
async def list_holidays(country: str, year: int):
    country = validate_country(country)
    year = validate_year(year)

    return {
        "country": country,
        "year": year,
        "holidays": [],
    }


@app.get("/api/v1/today")
async def today(country: str):
    country = validate_country(country)

    return {
        "country": country,
        "date": date.today().isoformat(),
        "holiday": None,
    }


Default = asgi.entrypoint(app)