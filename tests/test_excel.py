from datetime import date, time
from pathlib import Path

import pytest
from openpyxl import load_workbook

from bus_zeiterfassung.models import TimeEntry
from bus_zeiterfassung.services.excel import fill_template


def test_fill_template_writes_first_session_and_preserves_formulas(tmp_export_dir: Path) -> None:
    entries = [
        TimeEntry(day=date(2026, 4, 1), start=time(8, 0), end=time(12, 30)),
        TimeEntry(day=date(2026, 4, 2), start=time(9, 0), end=time(11, 0)),
    ]

    out = fill_template(entries, 2026, 4)

    assert out.exists()
    wb = load_workbook(out)
    ws = wb.active
    assert ws is not None

    assert ws["A1"].value == "Dienstzeitblatt für Monat: April"
    assert ws["G1"].value == "Jahr:"
    assert ws["H1"].value == 2026

    # Day 1 → row 7, day 2 → row 8. Session 1 goes into B/C.
    assert ws["B7"].value == time(8, 0)
    assert ws["C7"].value == time(12, 30)
    assert ws["B8"].value == time(9, 0)
    assert ws["C8"].value == time(11, 0)

    # Formula cells must remain formulas (openpyxl represents them as strings starting with "=").
    assert isinstance(ws["J7"].value, str) and ws["J7"].value.startswith("=")
    assert isinstance(ws["K7"].value, str) and ws["K7"].value.startswith("=")
    assert isinstance(ws["J38"].value, str) and ws["J38"].value.startswith("=")


def test_fill_template_skips_entries_outside_month(tmp_export_dir: Path) -> None:
    entries = [
        TimeEntry(day=date(2026, 3, 31), start=time(8, 0), end=time(9, 0)),
        TimeEntry(day=date(2026, 4, 1), start=time(8, 0), end=time(9, 0)),
        TimeEntry(day=date(2026, 5, 1), start=time(8, 0), end=time(9, 0)),
    ]

    out = fill_template(entries, 2026, 4)
    wb = load_workbook(out)
    ws = wb.active
    assert ws is not None

    assert ws["B7"].value == time(8, 0)  # April 1
    # March 31 would be row 37, but we filtered it out — cell stays empty.
    assert ws["B37"].value is None


def test_fill_template_ignores_entries_without_start(tmp_export_dir: Path) -> None:
    entries = [TimeEntry(day=date(2026, 4, 1), start=None, end=None)]
    out = fill_template(entries, 2026, 4)
    wb = load_workbook(out)
    ws = wb.active
    assert ws is not None
    assert ws["B7"].value is None


@pytest.mark.parametrize(
    ("month", "name"),
    [(1, "Januar"), (3, "März"), (7, "Juli"), (12, "Dezember")],
)
def test_german_month_in_header(tmp_export_dir: Path, month: int, name: str) -> None:
    out = fill_template([], 2026, month)
    wb = load_workbook(out)
    ws = wb.active
    assert ws is not None
    assert ws["A1"].value == f"Dienstzeitblatt für Monat: {name}"
