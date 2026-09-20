from pathlib import Path
from typing import Any

import yaml


ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT / "data"


class DataError(Exception):
    pass


def load_country(country: str) -> dict[str, Any]:
    country = country.upper()

    if len(country) != 2 or not country.isalpha():
        raise DataError(
            "Country must be a two-letter ISO 3166-1 code."
        )

    path = DATA_DIR / f"{country.lower()}.yml"

    if not path.is_file():
        raise DataError(
            f"Country '{country}' is not currently supported."
        )

    try:
        with path.open("r", encoding="utf-8") as file:
            document = yaml.safe_load(file)
    except yaml.YAMLError as exc:
        raise DataError(
            f"Invalid YAML in {path.name}."
        ) from exc

    if not isinstance(document, dict) or country not in document:
        raise DataError(
            f"Invalid data file for country '{country}'."
        )

    data = document[country]

    if not isinstance(data, dict):
        raise DataError(
            f"Invalid country data for '{country}'."
        )

    return data


def get_subdivision(
    country_data: dict[str, Any],
    subdivision: str
) -> dict[str, Any] | None:
    subdivisions = country_data.get("subdivisions", {})

    if not isinstance(subdivisions, dict):
        return None

    return subdivisions.get(subdivision.upper())


def get_country_codes() -> list[str]:
    if not DATA_DIR.is_dir():
        return []

    return sorted(
        path.stem.upper()
        for path in DATA_DIR.glob("*.yml")
        if path.is_file()
    )