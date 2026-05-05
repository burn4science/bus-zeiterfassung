from datetime import date, timedelta

from fastapi import HTTPException
from sqlmodel import Session, select

from bus_zeiterfassung.models import TimeEntry
from bus_zeiterfassung.timeutil import month_date_range, today_local


class TimeEntryStore:
    def __init__(self, session: Session) -> None:
        self._session = session

    def get_by_day(self, day: date) -> list[TimeEntry]:
        return list(self._session.exec(
            select(TimeEntry).where(TimeEntry.day == day).order_by(TimeEntry.start)  # type: ignore[arg-type]
        ))

    def get_by_month(self, year: int, month: int) -> list[TimeEntry]:
        start, end = month_date_range(year, month)
        return list(self._session.exec(
            select(TimeEntry)
            .where(TimeEntry.day >= start, TimeEntry.day < end)
            .order_by(TimeEntry.day, TimeEntry.start)  # type: ignore[arg-type]
        ))

    def get_open_today(self) -> TimeEntry | None:
        return self._session.exec(
            select(TimeEntry)
            .where(TimeEntry.day == today_local(), TimeEntry.end.is_(None))  # type: ignore[union-attr]
            .order_by(TimeEntry.start.desc())  # type: ignore[union-attr]
        ).first()

    def get_by_id_or_404(self, entry_id: int) -> TimeEntry:
        entry = self._session.get(TimeEntry, entry_id)
        if entry is None:
            raise HTTPException(status_code=404)
        return entry

    def next_nav_day(self, viewing_day: date, today: date) -> tuple[date, bool]:
        """Past days step day-by-day; today/future jump to the nearest entry."""
        if viewing_day < today:
            return viewing_day + timedelta(days=1), True
        next_entry = self._session.exec(
            select(TimeEntry)
            .where(TimeEntry.day > viewing_day)  # type: ignore[arg-type]
            .order_by(TimeEntry.day)  # type: ignore[arg-type]
            .limit(1)
        ).first()
        if next_entry:
            return next_entry.day, True
        return viewing_day + timedelta(days=1), False

    def save(self, entry: TimeEntry) -> None:
        self._session.add(entry)
        self._session.commit()

    def delete(self, entry: TimeEntry) -> None:
        self._session.delete(entry)
        self._session.commit()
