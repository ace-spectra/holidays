from datetime import date


WEEKDAYS = {
    "monday": 0,
    "tuesday": 1,
    "wednesday": 2,
    "thursday": 3,
    "friday": 4,
    "saturday": 5,
    "sunday": 6,
}


def _get_date(
    expression: str,
    context: dict[str, date]
) -> date | None:
    expression = expression.strip().lower()

    if expression in context:
        return context[expression]

    parts = expression.split(".")

    if len(parts) != 3:
        return None

    month_name, day, attribute = parts

    try:
        day = int(day)
    except ValueError:
        return None

    for key, value in context.items():
        if key.lower() == month_name:
            try:
                return value.replace(day=day)
            except ValueError:
                return None

    return None


def evaluate_condition(
    condition: str | None,
    context: dict[str, date]
) -> bool:
    if not condition:
        return True

    for expression in condition.split("||"):
        expression = expression.strip()

        if "==" not in expression:
            continue

        left, right = expression.split("==", 1)

        left = left.strip()
        right = right.strip().strip("'\"").lower()

        if left.lower() == "substitutes.weekday":
            reference = context.get("substitutes")

            if reference is not None:
                if reference.strftime("%A").lower() == right:
                    return True

            continue

        parts = left.split(".")

        if len(parts) == 3 and parts[2].lower() == "weekday":
            month = parts[0].lower()

            try:
                day = int(parts[1])
            except ValueError:
                continue

            reference = None

            for key, value in context.items():
                if key.lower() == month:
                    try:
                        reference = value.replace(day=day)
                    except ValueError:
                        reference = None
                    break

            if reference is not None:
                if reference.strftime("%A").lower() == right:
                    return True

    return False