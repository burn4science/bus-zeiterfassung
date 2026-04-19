from datetime import date, timedelta
from typing import Annotated

from fastapi import APIRouter, Depends, Form, Query, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlmodel import Session, select

from bus_zeiterfassung.auth import SESSION_KEY, require_login, verify_pin
from bus_zeiterfassung.db import get_session
from bus_zeiterfassung.models import TimeEntry
from bus_zeiterfassung.routes.entries import _next_nav_day
from bus_zeiterfassung.templating import templates
from bus_zeiterfassung.timeutil import today_local

router = APIRouter()


@router.get("/login", response_class=HTMLResponse)
def login_page(request: Request) -> HTMLResponse:
    return templates.TemplateResponse(request, "login.html", {"error": None})


@router.post("/login", response_model=None)
def login_submit(
    request: Request,
    pin: Annotated[str, Form()],
) -> HTMLResponse | RedirectResponse:
    if not verify_pin(pin):
        return templates.TemplateResponse(
            request, "login.html", {"error": "Falsche PIN"}, status_code=401
        )
    request.session[SESSION_KEY] = True
    return RedirectResponse(url="/", status_code=303)


@router.post("/logout")
def logout(request: Request) -> RedirectResponse:
    request.session.clear()
    return RedirectResponse(url="/login", status_code=303)


@router.get("/", response_class=HTMLResponse, dependencies=[Depends(require_login)])
def today_page(
    request: Request,
    session: Annotated[Session, Depends(get_session)],
    day_str: Annotated[str | None, Query(alias="d")] = None,
) -> HTMLResponse:
    today = today_local()
    selected_day = date.fromisoformat(day_str) if day_str else today
    stmt = select(TimeEntry).where(TimeEntry.day == selected_day).order_by(TimeEntry.start)  # type: ignore[arg-type]
    entries = list(session.exec(stmt))
    open_entry = next((e for e in entries if e.start is not None and e.end is None), None)
    next_day, has_next = _next_nav_day(session, selected_day, today)
    return templates.TemplateResponse(
        request,
        "today.html",
        {
            "today": today,
            "selected_day": selected_day,
            "is_today": selected_day == today,
            "prev_day": selected_day - timedelta(days=1),
            "next_day": next_day,
            "has_next": has_next,
            "entries": entries,
            "open_entry": open_entry,
        },
    )


@router.get("/month", response_class=HTMLResponse, dependencies=[Depends(require_login)])
def month_page(
    request: Request,
    session: Annotated[Session, Depends(get_session)],
    month_str: Annotated[str | None, Query(alias="m")] = None,
) -> HTMLResponse:
    today = today_local()
    if month_str:
        year, month = (int(part) for part in month_str.split("-", 1))
    else:
        year, month = today.year, today.month

    start = date(year, month, 1)
    end = date(year + (month == 12), (month % 12) + 1, 1)
    stmt = (
        select(TimeEntry)
        .where(TimeEntry.day >= start, TimeEntry.day < end)
        .order_by(TimeEntry.day, TimeEntry.start)  # type: ignore[arg-type]
    )
    entries = list(session.exec(stmt))
    prev_month, prev_year = (12, year - 1) if month == 1 else (month - 1, year)
    next_month, next_year = (1, year + 1) if month == 12 else (month + 1, year)
    return templates.TemplateResponse(
        request,
        "month.html",
        {
            "year": year, "month": month, "entries": entries,
            "month_key": f"{year}-{month:02d}",
            "prev_key": f"{prev_year}-{prev_month:02d}",
            "next_key": f"{next_year}-{next_month:02d}",
            "is_future": date(next_year, next_month, 1) > today,
            "is_current_month": year == today.year and month == today.month,
        },
    )
