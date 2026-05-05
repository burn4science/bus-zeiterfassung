from datetime import date, datetime, time
from zoneinfo import ZoneInfo

from bus_zeiterfassung.config import settings


def _tz() -> ZoneInfo:
    return ZoneInfo(settings.tz)


def now_local() -> datetime:
    return datetime.now(tz=_tz())


def today_local() -> date:
    return now_local().date()


def now_time_local() -> time:
    return now_local().time().replace(microsecond=0)


def month_date_range(year: int, month: int) -> tuple[date, date]:
    start = date(year, month, 1)
    end = date(year + (month == 12), (month % 12) + 1, 1)
    return start, end


def parse_month_key(month_key: str) -> tuple[int, int]:
    try:
        y_s, m_s = month_key.split("-", 1)
        y, m = int(y_s), int(m_s)
        if not (1 <= m <= 12) or y < 2000:
            raise ValueError
    except ValueError as e:
        raise ValueError("Monat erwartet Format YYYY-MM") from e
    return y, m


def validate_time_range(start: time, end: time | None) -> None:
    if end is not None and end <= start:
        raise ValueError("Ende muss nach Start liegen")
