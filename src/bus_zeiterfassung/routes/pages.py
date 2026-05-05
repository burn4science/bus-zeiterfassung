from datetime import date, timedelta
from typing import Annotated

from fastapi import APIRouter, Depends, Form, HTTPException, Query, Request
from fastapi.responses import HTMLResponse, RedirectResponse

from bus_zeiterfassung.auth import SESSION_KEY, require_login, verify_pin
from bus_zeiterfassung.db import get_store
from bus_zeiterfassung.store import TimeEntryStore
from bus_zeiterfassung.templating import templates
from bus_zeiterfassung.timeutil import parse_month_key, today_local

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
    store: Annotated[TimeEntryStore, Depends(get_store)],
    day_str: Annotated[str | None, Query(alias="d")] = None,
) -> HTMLResponse:
    today = today_local()
    selected_day = date.fromisoformat(day_str) if day_str else today
    entries = store.get_by_day(selected_day)
    open_entry = next((e for e in entries if e.start is not None and e.end is None), None)
    next_day, has_next = store.next_nav_day(selected_day, today)
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
    store: Annotated[TimeEntryStore, Depends(get_store)],
    month_str: Annotated[str | None, Query(alias="m")] = None,
) -> HTMLResponse:
    today = today_local()
    if month_str:
        try:
            year, month = parse_month_key(month_str)
        except ValueError:
            raise HTTPException(status_code=400, detail="Monat erwartet Format YYYY-MM")
    else:
        year, month = today.year, today.month

    entries = store.get_by_month(year, month)
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
