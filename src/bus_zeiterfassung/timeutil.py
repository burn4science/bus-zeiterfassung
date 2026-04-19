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
