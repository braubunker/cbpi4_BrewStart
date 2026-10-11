from datetime import datetime

import pytest

from cbpi4_BrewStart.schedule import (
    format_countdown,
    format_start,
    parse_time,
    resolve_start,
)


def test_parse_time_hhmm():
    assert parse_time("06:30") == (6, 30, 0)


def test_parse_time_hhmmss():
    assert parse_time("18:05:09") == (18, 5, 9)


def test_parse_time_invalid():
    with pytest.raises(ValueError):
        parse_time("25:00")


def test_resolve_today_future():
    now = datetime(2026, 10, 10, 5, 0, 0)
    start = resolve_start("Today", "06:00", now=now)
    assert start == datetime(2026, 10, 10, 6, 0, 0)


def test_resolve_today_already_past_uses_tomorrow():
    now = datetime(2026, 10, 10, 7, 0, 0)
    start = resolve_start("Today", "06:00", now=now)
    assert start == datetime(2026, 10, 11, 6, 0, 0)


def test_resolve_daily_same_as_next_occurrence():
    now = datetime(2026, 10, 10, 21, 0, 0)
    start = resolve_start("Daily", "05:30", now=now)
    assert start == datetime(2026, 10, 11, 5, 30, 0)


def test_resolve_datetime_split_fields():
    now = datetime(2026, 10, 1, 12, 0, 0)
    start = resolve_start(
        "DateTime",
        start_time="06:15",
        start_date="2026-10-12",
        now=now,
    )
    assert start == datetime(2026, 10, 12, 6, 15, 0)


def test_resolve_datetime_german_format_in_date_field():
    start = resolve_start(
        "DateTime",
        start_time="",
        start_date="12.10.2026 06:15",
        now=datetime(2026, 10, 1, 0, 0, 0),
    )
    assert start == datetime(2026, 10, 12, 6, 15, 0)


def test_resolve_datetime_waitstep_format():
    start = resolve_start(
        "DateTime",
        start_time="",
        start_date="12.10.26-06:15",
        now=datetime(2026, 10, 1, 0, 0, 0),
    )
    assert start == datetime(2026, 10, 12, 6, 15, 0)


def test_format_countdown():
    assert format_countdown(3661) == "1h 01m 01s"
    assert format_countdown(65) == "1m 05s"
    assert format_countdown(9) == "9s"
    assert format_countdown(-3) == "0s"


def test_format_start():
    assert format_start(datetime(2026, 10, 11, 6, 0)) == "11.10.2026 06:00"
