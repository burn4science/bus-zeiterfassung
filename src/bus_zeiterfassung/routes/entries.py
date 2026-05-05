from datetime import date, time, timedelta
from typing import Annotated

from fastapi import APIRouter, Depends, Form, HTTPException, Request
from fastapi.responses import HTMLResponse

from bus_zeiterfassung.auth import require_login
from bus_zeiterfassung.db import get_store
from bus_zeiterfassung.models import TimeEntry
from bus_zeiterfassung.store import TimeEntryStore
from bus_zeiterfassung.templating import templates
from bus_zeiterfassung.timeutil import now_time_local, today_local, validate_time_range

router = APIRouter(dependencies=[Depends(require_login)])


def _render_today_card(
    request: Request,
    store: TimeEntryStore,
    selected_day: date | None = None,
    flash: str | None = None,
) -> HTMLResponse:
    today = today_local()
    viewing_day = selected_day or today
    entries = store.get_by_day(viewing_day)
    open_entry = next((e for e in entries if e.start is not None and e.end is None), None)
    next_day, has_next = store.next_nav_day(viewing_day, today)
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
    store: Annotated[TimeEntryStore, Depends(get_store)],
) -> HTMLResponse:
    if store.get_open_today() is None:
        store.save(TimeEntry(day=today_local(), start=now_time_local(), end=None))
    return _render_today_card(request, store)


@router.post("/stop", response_class=HTMLResponse)
def stop(
    request: Request,
    store: Annotated[TimeEntryStore, Depends(get_store)],
) -> HTMLResponse:
    open_entry = store.get_open_today()
    if open_entry is not None:
        open_entry.end = now_time_local()
        store.save(open_entry)
    return _render_today_card(request, store)


@router.post("/entries", response_class=HTMLResponse)
def create_entry(
    request: Request,
    store: Annotated[TimeEntryStore, Depends(get_store)],
    day: Annotated[date, Form()],
    start: Annotated[time, Form()],
    end: Annotated[time | None, Form()] = None,
    note: Annotated[str | None, Form()] = None,
) -> HTMLResponse:
    try:
        validate_time_range(start, end)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
    store.save(TimeEntry(day=day, start=start, end=end, note=note))
    return _render_today_card(
        request, store, selected_day=day,
        flash=f"Eintrag für {day.strftime('%d.%m.%Y')} gespeichert",
    )


@router.post("/entries/{entry_id}/update", response_class=HTMLResponse)
def update_entry(
    entry_id: int,
    request: Request,
    store: Annotated[TimeEntryStore, Depends(get_store)],
    day: Annotated[date, Form()],
    start: Annotated[time, Form()],
    end: Annotated[time | None, Form()] = None,
    note: Annotated[str | None, Form()] = None,
    view: Annotated[str | None, Form()] = None,
    selected_day_str: Annotated[str | None, Form(alias="selected_day")] = None,
) -> HTMLResponse:
    entry = store.get_by_id_or_404(entry_id)
    try:
        validate_time_range(start, end)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
    entry.day = day
    entry.start = start
    entry.end = end
    entry.note = note
    store.save(entry)
    if view == "today":
        viewing_day = date.fromisoformat(selected_day_str) if selected_day_str else None
        return _render_today_card(request, store, selected_day=viewing_day)
    return templates.TemplateResponse(request, "partials/month_row.html", {"e": entry})


@router.post("/entries/{entry_id}/delete", response_class=HTMLResponse)
def delete_entry(
    entry_id: int,
    request: Request,
    store: Annotated[TimeEntryStore, Depends(get_store)],
    view: Annotated[str | None, Form()] = None,
    selected_day_str: Annotated[str | None, Form(alias="selected_day")] = None,
) -> HTMLResponse:
    entry = store.get_by_id_or_404(entry_id)
    store.delete(entry)
    if view == "today":
        viewing_day = date.fromisoformat(selected_day_str) if selected_day_str else None
        return _render_today_card(request, store, selected_day=viewing_day)
    return HTMLResponse("")
