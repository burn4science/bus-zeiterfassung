from datetime import date
from typing import Annotated

from fastapi import APIRouter, Depends, Form, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlmodel import Session, select

from bus_zeiterfassung.auth import SESSION_KEY, require_login, verify_pin
from bus_zeiterfassung.db import get_session
from bus_zeiterfassung.models import TimeEntry
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
) -> HTMLResponse:
    today = today_local()
    stmt = select(TimeEntry).where(TimeEntry.day == today).order_by(TimeEntry.start)  # type: ignore[arg-type]
    entries = list(session.exec(stmt))
    open_entry = next((e for e in entries if e.start is not None and e.end is None), None)
    return templates.TemplateResponse(
        request,
        "today.html",
        {"today": today, "entries": entries, "open_entry": open_entry},
    )


@router.get("/month", response_class=HTMLResponse, dependencies=[Depends(require_login)])
def month_page(
    request: Request,
    session: Annotated[Session, Depends(get_session)],
    m: str | None = None,
) -> HTMLResponse:
    today = today_local()
    if m:
        y, mo = (int(x) for x in m.split("-", 1))
    else:
        y, mo = today.year, today.month

    start = date(y, mo, 1)
    end = date(y + (mo == 12), (mo % 12) + 1, 1)
    stmt = (
        select(TimeEntry)
        .where(TimeEntry.day >= start, TimeEntry.day < end)
        .order_by(TimeEntry.day, TimeEntry.start)  # type: ignore[arg-type]
    )
    entries = list(session.exec(stmt))
    return templates.TemplateResponse(
        request,
        "month.html",
        {"year": y, "month": mo, "entries": entries, "month_key": f"{y}-{mo:02d}"},
    )
