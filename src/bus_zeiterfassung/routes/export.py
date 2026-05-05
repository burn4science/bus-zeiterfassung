from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse

from bus_zeiterfassung.auth import require_login
from bus_zeiterfassung.db import get_store
from bus_zeiterfassung.services.excel import fill_template
from bus_zeiterfassung.services.pdf import PdfConversionError, xlsx_to_pdf
from bus_zeiterfassung.store import TimeEntryStore
from bus_zeiterfassung.timeutil import parse_month_key

router = APIRouter(dependencies=[Depends(require_login)])


@router.post("/export/{month_key}")
def export_pdf(
    month_key: str,
    store: Annotated[TimeEntryStore, Depends(get_store)],
) -> FileResponse:
    try:
        year, month = parse_month_key(month_key)
    except ValueError:
        raise HTTPException(status_code=400, detail="Monat erwartet Format YYYY-MM")
    entries = store.get_by_month(year, month)
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
