from __future__ import annotations

from collections.abc import Callable
from pathlib import Path

import pytest
from pypdf import PdfWriter

from resume_builder.infra.pdf import PdfRenderResult

type Payload = dict[str, object]
type PdfRenderer = Callable[[Path, Path], PdfRenderResult]
type PdfRendererFactory = Callable[[dict[str, int]], PdfRenderer]


@pytest.fixture
def sample_payload() -> Payload:
    return {
        "contato": {
            "nome": "Ana Silva",
            "titulo": "Engenheira de Software",
            "email": "ana@email.com",
            "linkedin": "https://linkedin.com/in/ana",
            "github": "https://github.com/ana",
        },
        "resumo": "Engenheira com foco em backend, performance e entrega de produtos digitais.",
        "experiencias": [
            {
                "empresa": "Empresa X",
                "cargo": "Software Engineer",
                "inicio": "2022-01",
                "fim": "2024-12",
                "bullets": [
                    "Implementei pipeline que reduziu latencia em 35%.",
                    "Liderei squad de 6 pessoas para migracao sem downtime.",
                ],
                "tecnologias": ["Python", "FastAPI", "PostgreSQL"],
            }
        ],
        "educacao": [
            {
                "instituicao": "Universidade Y",
                "curso": "Ciencia da Computacao",
                "inicio": "2017",
                "fim": "2021",
            }
        ],
        "skills": ["Python", "FastAPI", "SQL", "Docker"],
        "projetos": [
            {
                "nome": "Portal de Indicadores",
                "resumo": "Painel de monitoramento operacional.",
                "bullets": ["Desenvolvi API com 99.9% de disponibilidade em 2024."],
                "tecnologias": ["Python", "Redis"],
            }
        ],
        "certificacoes": [{"nome": "AWS Cloud Practitioner", "emissor": "AWS", "ano": "2023"}],
        "idiomas": [{"idioma": "Ingles", "nivel": "Avancado"}],
    }


@pytest.fixture
def fake_pdf_renderer() -> PdfRenderer:
    def _render(_html_path: Path, output_pdf: Path) -> PdfRenderResult:
        writer = PdfWriter()
        writer.add_blank_page(width=595, height=842)
        with output_pdf.open("wb") as handle:
            writer.write(handle)

        return PdfRenderResult(engine="fake", pages=1, output_path=output_pdf)

    return _render


@pytest.fixture
def profile_pdf_renderer() -> PdfRendererFactory:
    def _factory(pages_by_profile: dict[str, int]) -> PdfRenderer:
        def _render(_html_path: Path, output_pdf: Path) -> PdfRenderResult:
            stem_parts = output_pdf.stem.split(".")
            profile = stem_parts[-1] if stem_parts else "padrao"
            pages = pages_by_profile.get(profile, 1)

            writer = PdfWriter()
            for _ in range(max(1, pages)):
                writer.add_blank_page(width=595, height=842)
            with output_pdf.open("wb") as handle:
                writer.write(handle)

            return PdfRenderResult(engine="fake", pages=pages, output_path=output_pdf)

        return _render

    return _factory
