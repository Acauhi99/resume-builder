from __future__ import annotations

import json
from collections.abc import Callable
from pathlib import Path

import yaml

from resume_builder.infra.pdf import PdfRenderResult
from resume_builder.infra.pipeline import build_resume
from resume_builder.infra.scaffold import create_project_scaffold


def test_build_pipeline_generates_html_score_and_pdf(
    tmp_path: Path,
    sample_payload: dict[str, object],
    fake_pdf_renderer: Callable[[Path, Path], PdfRenderResult],
) -> None:
    create_project_scaffold(tmp_path)

    data_path = tmp_path / "data" / "resume.yaml"
    with data_path.open("w", encoding="utf-8") as handle:
        yaml.safe_dump(sample_payload, handle, allow_unicode=True, sort_keys=False)

    result = build_resume(
        input_yaml=data_path,
        template_html=tmp_path / "templates" / "resume.html",
        template_css=tmp_path / "templates" / "resume.css",
        dist_dir=tmp_path / "dist",
        render_pdf_fn=fake_pdf_renderer,
    )

    assert result.html_path.exists()
    assert result.pdf_path is not None and result.pdf_path.exists()
    assert result.score_json_path.exists()
    assert result.score_md_path.exists()

    payload = json.loads(result.score_json_path.read_text(encoding="utf-8"))
    assert "pontuacao_total" in payload
    assert payload["idioma"] == "pt-BR"
