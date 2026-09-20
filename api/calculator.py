from calendar import monthrange
from datetime import date, timedelta
from typing import Any

from conditions import evaluate_condition
from models import Holiday


MONTHS = {
    "january": 1,
    "february": 2,
    "march": 3,
    "april": 4,
    "may": 5,
    "june": 6,
    "july": 7,
    "august": 8,
    "september": 9,
    "october": 10,
    "november": 11,
    "december": 12,
}

WEEKDAYS = {
    "monday": 0,
    "tuesday": 1,
    "wednesday": 2,
    "thursday": 3,
    "friday": 4,
    "saturday": 5,
    "sunday": 6,
}


def easter(year: int) -> date:
    a = year % 19
    b = year // 100
    c = year % 100
    d = b // 4
    e = b % 4
    f = (b + 8) // 25
    g = (b - f + 1) // 3
    h = (19 * a + b - d - g + 15) % 30
    i = c // 4
    k = c % 4
    l = (32 + 2 * e + 2 * i - h - k) % 7
    m = (a + 11 * h + 22 * l) // 451

    month = (h + l - 7 * m + 114) // 31
    day = ((h + l - 7 * m + 114) % 31) + 1

    return date(year, month, day)


def parse_fixed(value: list[Any], year: int) -> date:
    if len(value) != 2:
        raise ValueError("Fixed date must contain month and day.")

    month = value[0]
    day = value[1]

    if isinstance(month, str):
        month_number = MONTHS.get(month.lower())
    else:
        month_number = int(month)

    if not month_number:
        raise ValueError(f"Unknown month: {month}")

    return date(year, month_number, int(day))


def first_weekday(
    year: int,
    month: int,
    weekday: int
) -> date:
    first = date(year, month, 1)
    offset = (weekday - first.weekday()) % 7
    return first + timedelta(days=offset)


def last_weekday(
    year: int,
    month: int,
    weekday: int
) -> date:
    last_day = monthrange(year, month)[1]
    last = date(year, month, last_day)
    offset = (last.weekday() - weekday) % 7
    return last - timedelta(days=offset)


def calculate_rule(
    rule: dict[str, Any],
    year: int
) -> date | None:
    start_year = rule.get("startYear")

    if start_year is not None and year < int(start_year):
        return None

    end_year = rule.get("endYear")

    if end_year is not None and year > int(end_year):
        return None

    if "fixed" in rule:
        return parse_fixed(rule["fixed"], year)

    computed = rule.get("computed")

    if not computed:
        return None

    if "computus" in computed:
        offset = int(computed["computus"])
        return easter(year) + timedelta(days=offset)

    first = computed.get("first")

    if first:
        weekday = WEEKDAYS[first["weekday"].lower()]
        month = MONTHS[first["in"].lower()]

        return first_weekday(
            year,
            month,
            weekday
        )

    last = computed.get("last")

    if last:
        weekday = WEEKDAYS[last["weekday"].lower()]
        month = MONTHS[last["in"].lower()]

        return last_weekday(
            year,
            month,
            weekday
        )

    return None


def get_sources(
    holiday_group: dict[str, Any]
) -> tuple[str, ...]:
    sources = holiday_group.get("sources", [])

    if not isinstance(sources, list):
        return ()

    return tuple(str(source) for source in sources)


def build_context(
    rules: list[dict[str, Any]],
    year: int
) -> dict[str, date]:
    context: dict[str, date] = {}

    for rule in rules:
        holiday_date = calculate_rule(rule, year)

        if holiday_date is None:
            continue

        if "fixed" in rule:
            fixed = rule["fixed"]

            if len(fixed) == 2:
                month = str(fixed[0]).lower()

                if month in MONTHS:
                    context[month] = holiday_date

        context.setdefault(
            "substitutes",
            holiday_date
        )

    return context


def calculate_holidays(
    country_data: dict[str, Any],
    year: int,
    subdivision: str | None = None
) -> list[Holiday]:
    holidays: list[Holiday] = []

    holiday_groups = country_data.get("holidays", {})

    if not isinstance(holiday_groups, dict):
        return holidays

    if subdivision:
        subdivisions = country_data.get("subdivisions", {})
        subdivision_data = subdivisions.get(subdivision.upper())

        if isinstance(subdivision_data, dict):
            subdivision_holidays = subdivision_data.get(
                "holidays",
                {}
            )

            if isinstance(subdivision_holidays, dict):
                holiday_groups = {
                    **holiday_groups,
                    **subdivision_holidays,
                }

    for holiday_id, group in holiday_groups.items():
        if not isinstance(group, dict):
            continue

        rules = group.get("dates", [])

        if not isinstance(rules, list):
            continue

        sources = get_sources(group)
        context = build_context(rules, year)

        for rule in rules:
            if not isinstance(rule, dict):
                continue

            condition = rule.get("condition")

            if condition and not evaluate_condition(
                condition,
                context
            ):
                continue

            holiday_date = calculate_rule(
                rule,
                year
            )

            if holiday_date is None:
                continue

            names = rule.get("name", {})

            if isinstance(names, dict):
                name = names.get("en")
                if name is None and names:
                    name = next(iter(names.values()))
            else:
                name = str(names)

            if not name:
                name = str(holiday_id)

            holidays.append(
                Holiday(
                    id=str(holiday_id),
                    name=str(name),
                    date=holiday_date,
                    type=str(
                        rule.get(
                            "type",
                            "public"
                        )
                    ),
                    substitute=bool(
                        rule.get(
                            "substitute",
                            False
                        )
                    ),
                    sources=sources,
                )
            )

    return sorted(
        holidays,
        key=lambda holiday: (
            holiday.date,
            holiday.name,
        )
    )