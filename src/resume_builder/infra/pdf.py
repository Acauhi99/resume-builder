from __future__ import annotations

import shutil
from dataclasses import dataclass
from pathlib import Path

from pypdf import PdfReader


@dataclass(frozen=True)
class PdfRenderResult:
    engine: str
    pages: int
    output_path: Path


class PdfRenderError(RuntimeError):
    pass


def count_pdf_pages(path: Path) -> int:
    reader = PdfReader(str(path))
    return len(reader.pages)


def _render_with_weasyprint(html_path: Path, output_pdf: Path) -> None:
    try:
        from weasyprint import HTML
    except Exception as exc:  # pragma: no cover - depende do ambiente.
        raise PdfRenderError(f"WeasyPrint indisponivel: {exc}") from exc

    try:
        HTML(filename=str(html_path), base_url=str(html_path.parent)).write_pdf(str(output_pdf))
    except Exception as exc:  # pragma: no cover - depende do ambiente.
        raise PdfRenderError(f"Falha ao renderizar PDF com WeasyPrint: {exc}") from exc


def _render_with_playwright(html_path: Path, output_pdf: Path) -> None:
    try:
        from playwright.sync_api import sync_playwright
    except Exception as exc:  # pragma: no cover - depende do ambiente.
        raise PdfRenderError(f"Playwright indisponivel: {exc}") from exc

    chrome_path = shutil.which("google-chrome") or shutil.which("chromium")

    try:
        with sync_playwright() as playwright:
            if chrome_path:
                browser = playwright.chromium.launch(
                    headless=True,
                    executable_path=chrome_path,
                )
            else:
                browser = playwright.chromium.launch(
                    headless=True,
                    channel="chrome",
                )
            page = browser.new_page()
            page.goto(html_path.resolve().as_uri(), wait_until="networkidle")
            page.pdf(
                path=str(output_pdf),
                format="A4",
                print_background=True,
                prefer_css_page_size=True,
                margin={"top": "0", "right": "0", "bottom": "0", "left": "0"},
            )
            browser.close()
    except Exception as exc:  # pragma: no cover - depende do ambiente.
        raise PdfRenderError(f"Falha ao renderizar PDF com Playwright: {exc}") from exc


def render_pdf_with_fallback(html_path: Path, output_pdf: Path) -> PdfRenderResult:
    errors: list[str] = []

    for engine_name, fn in (
        ("weasyprint", _render_with_weasyprint),
        ("playwright", _render_with_playwright),
    ):
        try:
            fn(html_path, output_pdf)
            pages = count_pdf_pages(output_pdf)
            return PdfRenderResult(engine=engine_name, pages=pages, output_path=output_pdf)
        except Exception as exc:
            errors.append(f"{engine_name}: {exc}")

    details = " | ".join(errors) if errors else "sem detalhes"
    raise PdfRenderError(f"Nenhum engine de PDF conseguiu renderizar: {details}")
