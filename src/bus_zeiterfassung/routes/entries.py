from datetime import date, time, timedelta
from typing import Annotated

from fastapi import APIRouter, Depends, Form, HTTPException, Request
from fastapi.responses import HTMLResponse
from sqlmodel import Session, select

from bus_zeiterfassung.auth import require_login
from bus_zeiterfassung.db import get_session
from bus_zeiterfassung.models import TimeEntry
from bus_zeiterfassung.templating import templates
from bus_zeiterfassung.timeutil import now_time_local, today_local

router = APIRouter(dependencies=[Depends(require_login)])


def _open_entry_for_today(session: Session) -> TimeEntry | None:
    stmt = (
        select(TimeEntry)
        .where(TimeEntry.day == today_local(), TimeEntry.end.is_(None))  # type: ignore[union-attr]
        .order_by(TimeEntry.start.desc())  # type: ignore[union-attr]
    )
    return session.exec(stmt).first()


def _next_nav_day(session: Session, viewing_day: date, today: date) -> tuple[date, bool]:
    """Return (next_nav_day, has_next). Past days go day-by-day; today/future jump to the nearest entry."""
    if viewing_day < today:
        return viewing_day + timedelta(days=1), True
    next_entry = session.exec(
        select(TimeEntry)
        .where(TimeEntry.day > viewing_day)  # type: ignore[arg-type]
        .order_by(TimeEntry.day)  # type: ignore[arg-type]
        .limit(1)
    ).first()
    if next_entry:
        return next_entry.day, True
    return viewing_day + timedelta(days=1), False


def _render_today_card(
    request: Request,
    session: Session,
    selected_day: date | None = None,
    flash: str | None = None,
) -> HTMLResponse:
    today = today_local()
    viewing_day = selected_day or today
    entries = list(session.exec(
        select(TimeEntry).where(TimeEntry.day == viewing_day).order_by(TimeEntry.start)  # type: ignore[arg-type]
    ))
    open_entry = next((e for e in entries if e.start is not None and e.end is None), None)
    next_day, has_next = _next_nav_day(session, viewing_day, today)
    return templates.TemplateResponse(
        request,
        "partials/today_card.html",
        {
            "today": today,
            "selected_day": viewing_day,
            "is_today": viewing_day == today,
            "prev_day": viewing_day - timedelta(days=1),
            "next_day": next_day,
            "has_next": has_next,
            "entries": entries,
            "open_entry": open_entry,
            "flash": flash,
        },
    )


@router.post("/start", response_class=HTMLResponse)
def start(
    request: Request,
    session: Annotated[Session, Depends(get_session)],
) -> HTMLResponse:
    open_entry = _open_entry_for_today(session)
    if open_entry is None:
        entry = TimeEntry(day=today_local(), start=now_time_local(), end=None)
        session.add(entry)
        session.commit()
    return _render_today_card(request, session)


@router.post("/stop", response_class=HTMLResponse)
def stop(
    request: Request,
    session: Annotated[Session, Depends(get_session)],
) -> HTMLResponse:
    open_entry = _open_entry_for_today(session)
    if open_entry is not None:
        open_entry.end = now_time_local()
        session.add(open_entry)
        session.commit()
    return _render_today_card(request, session)


@router.post("/entries", response_class=HTMLResponse)
def create_entry(
    request: Request,
    session: Annotated[Session, Depends(get_session)],
    day: Annotated[date, Form()],
    start: Annotated[time, Form()],
    end: Annotated[time | None, Form()] = None,
    note: Annotated[str | None, Form()] = None,
) -> HTMLResponse:
    if end is not None and end <= start:
        raise HTTPException(status_code=400, detail="Ende muss nach Start liegen")
    entry = TimeEntry(day=day, start=start, end=end, note=note)
    session.add(entry)
    session.commit()
    return _render_today_card(request, session, selected_day=day, flash=f"Eintrag für {day.strftime('%d.%m.%Y')} gespeichert")


@router.post("/entries/{entry_id}/update", response_class=HTMLResponse)
def update_entry(
    entry_id: int,
    request: Request,
    session: Annotated[Session, Depends(get_session)],
    day: Annotated[date, Form()],
    start: Annotated[time, Form()],
    end: Annotated[time | None, Form()] = None,
    note: Annotated[str | None, Form()] = None,
    view: Annotated[str | None, Form()] = None,
    selected_day_str: Annotated[str | None, Form(alias="selected_day")] = None,
) -> HTMLResponse:
    entry = session.get(TimeEntry, entry_id)
    if entry is None:
        raise HTTPException(status_code=404)
    if end is not None and end <= start:
        raise HTTPException(status_code=400, detail="Ende muss nach Start liegen")
    entry.day = day
    entry.start = start
    entry.end = end
    entry.note = note
    session.add(entry)
    session.commit()
    if view == "today":
        viewing_day = date.fromisoformat(selected_day_str) if selected_day_str else None
        return _render_today_card(request, session, selected_day=viewing_day)
    return templates.TemplateResponse(request, "partials/month_row.html", {"e": entry})


@router.post("/entries/{entry_id}/delete", response_class=HTMLResponse)
def delete_entry(
    entry_id: int,
    request: Request,
    session: Annotated[Session, Depends(get_session)],
    view: Annotated[str | None, Form()] = None,
    selected_day_str: Annotated[str | None, Form(alias="selected_day")] = None,
) -> HTMLResponse:
    entry = session.get(TimeEntry, entry_id)
    if entry is None:
        raise HTTPException(status_code=404)
    session.delete(entry)
    session.commit()
    if view == "today":
        viewing_day = date.fromisoformat(selected_day_str) if selected_day_str else None
        return _render_today_card(request, session, selected_day=viewing_day)
    return HTMLResponse("")
