from __future__ import annotations

from pathlib import Path

import pytest
from pypdf import PdfWriter

from resume_builder.infra import pdf
from resume_builder.infra.pdf import PdfRenderError, render_pdf_with_fallback


def test_pdf_fallback_uses_playwright_when_weasyprint_fails(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    html_path = tmp_path / "resume.html"
    html_path.write_text("<html><body><p>ok</p></body></html>", encoding="utf-8")

    output_pdf = tmp_path / "resume.pdf"

    def _fail_weasy(*args: object, **kwargs: object) -> None:
        raise PdfRenderError("weasy failed")

    def _ok_playwright(_html: Path, out: Path) -> None:
        writer = PdfWriter()
        writer.add_blank_page(width=595, height=842)
        with out.open("wb") as handle:
            writer.write(handle)

    monkeypatch.setattr(pdf, "_render_with_weasyprint", _fail_weasy)
    monkeypatch.setattr(pdf, "_render_with_playwright", _ok_playwright)

    result = render_pdf_with_fallback(html_path, output_pdf)
    assert result.engine == "playwright"
    assert result.pages == 1
    assert output_pdf.exists()
