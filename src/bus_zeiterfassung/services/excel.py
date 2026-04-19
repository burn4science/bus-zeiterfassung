from collections import defaultdict
from collections.abc import Sequence
from datetime import date as _date
from datetime import datetime as _dt
from datetime import time as _time
from pathlib import Path

from openpyxl import load_workbook
from openpyxl.styles import Border, Font, Side
from openpyxl.worksheet.properties import PageSetupProperties

from bus_zeiterfassung.config import settings
from bus_zeiterfassung.models import TimeEntry

GERMAN_MONTHS = {
    1: "Januar",
    2: "Februar",
    3: "März",
    4: "April",
    5: "Mai",
    6: "Juni",
    7: "Juli",
    8: "August",
    9: "September",
    10: "Oktober",
    11: "November",
    12: "Dezember",
}

SESSION_COLS = (("B", "C"), ("D", "E"), ("F", "G"), ("H", "I"))

_THIN = Side(style="thin")
_GRID = Border(left=_THIN, right=_THIN, top=_THIN, bottom=_THIN)


def _apply_table_borders(ws) -> None:
    for row in ws.iter_rows(min_row=5, max_row=37, min_col=1, max_col=11):
        for cell in row:
            cell.border = _GRID


def fill_template(entries: Sequence[TimeEntry], year: int, month: int) -> Path:
    """Fill the Dienstzeitblatt template for a given month and write it to EXPORT_DIR.

    Cell layout is documented in docs/template-mapping.md. J7:J37 formulas are
    overwritten to sum all 4 sessions. K formulas are never touched.
    """
    wb = load_workbook(settings.template_path, keep_vba=False)
    ws = wb.active
    assert ws is not None

    ws["A1"] = f"Dienstzeitblatt für Monat: {GERMAN_MONTHS[month]}"
    ws["G1"] = "Jahr:"
    ws["H1"] = year
    ws["A3"] = "Name:"
    ws["B3"] = settings.user_name

    by_day: dict[int, list[TimeEntry]] = defaultdict(list)
    for e in entries:
        if e.day.year == year and e.day.month == month and e.start is not None:
            by_day[e.day.day].append(e)

    for day, sessions in by_day.items():
        sessions.sort(key=lambda e: e.start)  # type: ignore[arg-type,return-value]
        row = day + 6
        for idx, session in enumerate(sessions[:4]):
            start_col, end_col = SESSION_COLS[idx]
            ws[f"{start_col}{row}"] = session.start
            if session.end is not None:
                ws[f"{end_col}{row}"] = session.end

        total_min = sum(
            (_dt.combine(_date.min, s.end) - _dt.combine(_date.min, s.start)).seconds // 60
            for s in sessions
            if s.start is not None and s.end is not None
        )
        if total_min > 0:
            h, m = divmod(total_min, 60)
            # Use 1 second bias so LibreOffice's hh:mm floor never rounds down
            ws[f"J{row}"] = _time(h, m, 1)

    for col in "BCDEFGHIJ":
        for row_num in range(7, 38):
            ws[f"{col}{row_num}"].number_format = "hh:mm"
    ws["J38"].number_format = "hh:mm"  # sum of all hours / minutes
    ws["J38"].font = Font(size=11, bold=True)

    _apply_table_borders(ws)

    for row_num in range(1, 5):
        for cell in ws[row_num]:
            cell.font = Font(name="Calibri", size=11)
    for row_num in range(5, 7):
        for cell in ws[row_num]:
            cell.font = Font(name="Calibri", size=10)
    for row_num in range(7, 38):
        for cell in ws[row_num]:
            cell.font = Font(name="Calibri", size=11)
    for row_num in range(38, ws.max_row + 1):
        for cell in ws[row_num]:
            cell.font = Font(name="Calibri", size=10)

    ws.column_dimensions["A"].width = 6  # day column
    for col in "BCDEFGHI":
        ws.column_dimensions[col].width = 7  # sessions 1-4 columns
    ws.column_dimensions["K"].width = 20  # notes column

    ws.sheet_properties.pageSetUpPr = PageSetupProperties(fitToPage=True)
    ws.page_setup.orientation = "portrait"
    # ws.page_setup.fitToWidth = 1
    # ws.page_setup.fitToHeight = 1

    settings.export_dir.mkdir(parents=True, exist_ok=True)
    out_path = settings.export_dir / f"{year}-{month:02d}.xlsx"
    wb.save(out_path)
    return out_path
