import datetime
from functools import lru_cache
from typing import Any


@lru_cache(maxsize=8192)
def to_date(d_even: int) -> datetime.date:
    d_even = int(d_even)
    return datetime.date(d_even // 10000, d_even // 100 % 100, d_even % 100)


def to_optional_date(d_even: int | None) -> datetime.date | None:
    if not d_even:
        return None
    return to_date(d_even)


@lru_cache(maxsize=65536)
def to_time(h_even: int) -> datetime.time:
    h_even = int(h_even)
    return datetime.time(h_even // 10000, h_even // 100 % 100, h_even % 100)


def to_optional_time(h_even: int | None) -> datetime.time | None:
    if h_even is None:
        return None
    return to_time(h_even)


def to_optional_int(value: Any) -> int | None:
    if value is None:
        return None
    return int(value)


def to_optional_float(value: Any) -> float | None:
    if value is None:
        return None
    return float(value)


def to_optional_bool(value: Any) -> bool | None:
    if value is None:
        return None
    return bool(value)


def to_optional_str(value: Any) -> str | None:
    if value is None:
        return None
    return str(value)


def number_text_to_float(value: Any) -> float | None:
    if value is None or value == "":
        return None
    try:
        return float(str(value).replace(",", ""))
    except ValueError:
        return None
