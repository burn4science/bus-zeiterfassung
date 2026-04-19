import shutil
import subprocess
from pathlib import Path


class PdfConversionError(RuntimeError):
    pass


def xlsx_to_pdf(xlsx_path: Path) -> Path:
    """Convert an xlsx file to PDF using headless LibreOffice.

    The PDF is written next to the xlsx with the same stem. Raises
    PdfConversionError if LibreOffice is missing or returns non-zero.
    """
    soffice = shutil.which("soffice") or shutil.which("libreoffice")
    if soffice is None:
        raise PdfConversionError("LibreOffice (soffice) not found on PATH")

    out_dir = xlsx_path.parent
    try:
        subprocess.run(
            [soffice, "--headless", "--convert-to", "pdf", "--outdir", str(out_dir), str(xlsx_path)],
            check=True,
            capture_output=True,
            timeout=60,
        )
    except subprocess.CalledProcessError as e:
        raise PdfConversionError(f"soffice failed: {e.stderr.decode(errors='replace')}") from e
    except subprocess.TimeoutExpired as e:
        raise PdfConversionError("soffice timed out after 60s") from e

    pdf_path = out_dir / f"{xlsx_path.stem}.pdf"
    if not pdf_path.exists():
        raise PdfConversionError(f"expected output not found: {pdf_path}")
    return pdf_path
