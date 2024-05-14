import logging
import re
from datetime import date, datetime, time
from typing import Union
from dateutil import parser


def get_translation(
    value: str, translations: list, fallbackToOriginalValue: bool = False
):
    """Accepts a 2d list with 3 items. [ ["from", "to" "show"], ... ]"""
    if value is None:
        return value

    # Find a translation
    for i in translations:
        if i[0].lower() == value.lower():
            if len(i) == 3 and i[2] is False:  # Explicitly use None
                return None
            return i[1]

    # Return the original value if not found
    return value if fallbackToOriginalValue else None


def get_fields(parse_fields, zaak_source):
    result = {}

    for field_config in parse_fields:
        key = field_config["name"]
        val = zaak_source.get(field_config["from"])
        result[key] = field_config["parser"](val)

    return result


def to_date(value) -> Union[date, None]:
    if not value:
        return None

    if isinstance(value, datetime):
        return value.date()

    if isinstance(value, date):
        return value

    if isinstance(value, str):
        parsed_value = parser.isoparse(value).date()
        return parsed_value

    logging.error(f"Error parsing date, value: {value}")
    return None


def to_time(value) -> Union[str, None]:
    if not value:
        return None

    if isinstance(value, datetime):
        return to_time(value.time())

    if isinstance(value, time):
        return f"{value.hour:02}:{value.minute:02}"

    if isinstance(value, str):
        time_pattern = r"([0-9]{1,2})[\.,:;]([0-9]{1,2})"
        matches = re.match(time_pattern, value)
        if matches:
            hour = int(matches.group(1))
            minute = int(matches.group(2))

            if (0 <= hour <= 23 and 0 <= minute <= 59) or (hour == 24 and minute == 00):
                if minute < 6:
                    return f"{hour:02}:{minute}0"

                return f"{hour:02}:{minute:02}"

    logging.error(f"Error parsing time, value: {value}")
    return None


def to_datetime(value) -> Union[datetime, None]:
    if not value:
        return None

    if isinstance(value, datetime):
        return value

    if isinstance(value, date):
        return datetime(value.year, value.month, value.day)

    if isinstance(value, str):
        parsed_value = parser.isoparse(value)
        return parsed_value

    logging.error(f"Error parsing datetime, value: {value}")
    return None


def to_string(value):
    if not value:
        return None
    return str(value).strip()


def to_string_or_empty_string(value):
    if not value:
        return ""
    return str(value).strip()


def to_string_if_exists(zaak, key, default_value=None):
    return to_string(zaak[key]) if key in zaak else default_value


def to_int(value):
    if value == 0:
        return 0
    if not value:
        return None
    return int(value)


def to_bool(value):
    if not value:
        return False
    return True


def to_bool_if_exists(zaak, key):
    return to_bool(zaak[key]) if key in zaak else False
