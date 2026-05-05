from datetime import date, time

import pytest

from bus_zeiterfassung.timeutil import month_date_range, parse_month_key, validate_time_range


def test_parse_month_key_valid() -> None:
    assert parse_month_key("2026-04") == (2026, 4)
    assert parse_month_key("2025-12") == (2025, 12)
    assert parse_month_key("2000-01") == (2000, 1)


def test_parse_month_key_invalid_format() -> None:
    with pytest.raises(ValueError):
        parse_month_key("invalid")


def test_parse_month_key_out_of_range_month() -> None:
    with pytest.raises(ValueError):
        parse_month_key("2026-13")
    with pytest.raises(ValueError):
        parse_month_key("2026-00")


def test_parse_month_key_year_too_old() -> None:
    with pytest.raises(ValueError):
        parse_month_key("1999-01")


def test_month_date_range_mid_year() -> None:
    start, end = month_date_range(2026, 4)
    assert start == date(2026, 4, 1)
    assert end == date(2026, 5, 1)


def test_month_date_range_december_wraps_year() -> None:
    start, end = month_date_range(2026, 12)
    assert start == date(2026, 12, 1)
    assert end == date(2027, 1, 1)


def test_validate_time_range_valid() -> None:
    validate_time_range(time(8, 0), time(12, 0))
    validate_time_range(time(8, 0), None)


def test_validate_time_range_end_before_start() -> None:
    with pytest.raises(ValueError):
        validate_time_range(time(12, 0), time(8, 0))


def test_validate_time_range_end_equals_start() -> None:
    with pytest.raises(ValueError):
        validate_time_range(time(8, 0), time(8, 0))
