from __future__ import annotations

from pathlib import Path

import yaml

from resume_builder.infra.pipeline import render_html_only
from resume_builder.infra.scaffold import create_project_scaffold


def test_rendered_html_contains_sections_and_typography_tokens(
    tmp_path: Path,
    sample_payload: dict[str, object],
) -> None:
    create_project_scaffold(tmp_path)

    data_path = tmp_path / "data" / "resume.yaml"
    with data_path.open("w", encoding="utf-8") as handle:
        yaml.safe_dump(sample_payload, handle, allow_unicode=True, sort_keys=False)

    output_html = tmp_path / "dist" / "resume.html"

    render_html_only(
        input_yaml=data_path,
        template_html=tmp_path / "templates" / "resume.html",
        template_css=tmp_path / "templates" / "resume.css",
        output_html=output_html,
        target_score=90,
        language="pt-BR",
    )

    html = output_html.read_text(encoding="utf-8")
    assert 'id="experiencia"' in html
    assert 'id="educacao"' in html
    assert 'class="layout"' in html
    assert "--body-font-pt:" in html
    assert "{{" not in html
