from __future__ import annotations

import shutil
import subprocess
import tempfile
import urllib.request
from dataclasses import dataclass
from pathlib import Path


@dataclass
class PdfExtractionResult:
    pdf_path: Path | None
    first_page_text: str | None
    body_text: str | None
    download_error: str | None = None
    extract_error: str | None = None


def preprocess_pdf(
    pdf_url: str | None,
    *,
    download_timeout: int = 25,
    body_pages: int = 6,
) -> PdfExtractionResult:
    if not pdf_url:
        return PdfExtractionResult(pdf_path=None, first_page_text=None, body_text=None, download_error="missing_pdf_url")

    pdftotext_bin = shutil.which("pdftotext") or "/opt/homebrew/bin/pdftotext"
    if not Path(pdftotext_bin).exists():
        return PdfExtractionResult(pdf_path=None, first_page_text=None, body_text=None, extract_error="pdftotext_not_found")

    with tempfile.TemporaryDirectory(prefix="paper-daily-pdf-") as tmpdir:
        pdf_path = Path(tmpdir) / "paper.pdf"
        try:
            with urllib.request.urlopen(pdf_url, timeout=download_timeout) as response:
                pdf_path.write_bytes(response.read())
        except Exception as exc:
            return PdfExtractionResult(
                pdf_path=None,
                first_page_text=None,
                body_text=None,
                download_error=f"{type(exc).__name__}: {exc}",
            )

        try:
            first_page_text = run_pdftotext(pdftotext_bin, pdf_path, first_page=1, last_page=1)
            body_text = run_pdftotext(pdftotext_bin, pdf_path, first_page=1, last_page=body_pages)
        except Exception as exc:
            return PdfExtractionResult(
                pdf_path=pdf_path,
                first_page_text=None,
                body_text=None,
                extract_error=f"{type(exc).__name__}: {exc}",
            )

        return PdfExtractionResult(pdf_path=pdf_path, first_page_text=first_page_text, body_text=body_text)


def run_pdftotext(pdftotext_bin: str, pdf_path: Path, *, first_page: int, last_page: int) -> str:
    result = subprocess.run(
        [pdftotext_bin, "-f", str(first_page), "-l", str(last_page), str(pdf_path), "-"],
        check=True,
        capture_output=True,
        text=True,
    )
    return result.stdout
