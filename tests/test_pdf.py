import shutil
from datetime import date, time
from pathlib import Path

import pytest

from bus_zeiterfassung.models import TimeEntry
from bus_zeiterfassung.services.excel import fill_template
from bus_zeiterfassung.services.pdf import xlsx_to_pdf

pytestmark = pytest.mark.skipif(
    shutil.which("soffice") is None and shutil.which("libreoffice") is None,
    reason="LibreOffice not installed",
)


def test_xlsx_to_pdf_end_to_end(tmp_export_dir: Path) -> None:
    entries = [TimeEntry(day=date(2026, 4, 1), start=time(8, 0), end=time(12, 0))]
    xlsx = fill_template(entries, 2026, 4)
    pdf = xlsx_to_pdf(xlsx)
    assert pdf.exists()
    assert pdf.suffix == ".pdf"
    assert pdf.stat().st_size > 1000  # a real PDF, not an empty stub
    with pdf.open("rb") as fh:
        assert fh.read(4) == b"%PDF"
