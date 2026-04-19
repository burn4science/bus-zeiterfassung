from datetime import date
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse
from sqlmodel import Session, select

from bus_zeiterfassung.auth import require_login
from bus_zeiterfassung.db import get_session
from bus_zeiterfassung.models import TimeEntry
from bus_zeiterfassung.services.excel import fill_template
from bus_zeiterfassung.services.pdf import PdfConversionError, xlsx_to_pdf

router = APIRouter(dependencies=[Depends(require_login)])


def _parse_month(month_key: str) -> tuple[int, int]:
    try:
        y_s, m_s = month_key.split("-", 1)
        y, m = int(y_s), int(m_s)
        if not (1 <= m <= 12) or y < 2000:
            raise ValueError
    except ValueError as e:
        raise HTTPException(status_code=400, detail="Monat erwartet Format YYYY-MM") from e
    return y, m


@router.post("/export/{month_key}")
def export_pdf(
    month_key: str,
    session: Annotated[Session, Depends(get_session)],
) -> FileResponse:
    year, month = _parse_month(month_key)
    start = date(year, month, 1)
    end = date(year + (month == 12), (month % 12) + 1, 1)
    stmt = (
        select(TimeEntry)
        .where(TimeEntry.day >= start, TimeEntry.day < end)
        .order_by(TimeEntry.day, TimeEntry.start)  # type: ignore[arg-type]
    )
    entries = list(session.exec(stmt))

    xlsx_path = fill_template(entries, year, month)
    try:
        pdf_path = xlsx_to_pdf(xlsx_path)
    except PdfConversionError as e:
        raise HTTPException(status_code=500, detail=str(e)) from e

    return FileResponse(
        pdf_path,
        media_type="application/pdf",
        filename=pdf_path.name,
    )
