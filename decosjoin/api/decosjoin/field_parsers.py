import logging
import re
from datetime import date, datetime, time
from typing import Union

from dateutil import parser

from decosjoin.api.decosjoin.Exception import ParseError


def get_translation(value: str, translations: list, fallbackToOriginalValue: bool = False):
    """ Accepts a 2d list with 3 items. [ ["from", "to" "show"], ... ] """
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
        key = field_config['name']
        val = zaak_source.get(field_config['from'])
        result[key] = field_config['parser'](val)

    return result


def to_date(value) -> Union[date, None]:
    if not value:
        return None

    if type(value) == date:
        return value

    if type(value) == datetime:
        return value.date()

    if type(value) == str:
        parsed_value = parser.isoparse(value).date()
        return parsed_value

    raise ParseError(f"Unable to parse type({type(value)} with to_date")


def to_time(value) -> Union[str, None]:
    if not value:
        return None

    if type(value) == time:
        return f'{value.hour:02}:{value.minute:02}'

    if type(value) == datetime:
        return to_time(value.time())

    if type(value) == str:
        time_pattern = r'([0-9]{2})[\.:]([0-9]{2})'
        matches = re.match(time_pattern, value)
        if matches:
            hour = int(matches.group(1))
            minute = int(matches.group(2))

            if (0 <= hour <= 23 and 0 <= minute <= 59) or (hour == 24 and minute == 00):
                return f'{hour:02}:{minute:02}'
            logging.error(f"Error parsing time, value: {value}")
            return None

    return None


def to_datetime(value) -> Union[datetime, None]:
    if not value:
        return None

    if type(value) == date:
        return datetime(value.year, value.month, value.day)

    if type(value) == datetime:
        return value

    if type(value) == str:
        parsed_value = parser.isoparse(value)
        return parsed_value

    raise ParseError(f"Unable to parse type({type(value)} with to_datetime")


def to_string(value):
    if not value:
        return None
    return str(value).strip()


def to_string_or_empty_string(value):
    if not value:
        return ''
    return str(value).strip()


def to_string_if_exists(zaak, key, default_value=None):
    return to_string(zaak[key]) if key in zaak else default_value


def to_int(value):
    if value == 0:
        return 0
    if not value:
        return None
    return int(value)
