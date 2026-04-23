from __future__ import annotations

from collections.abc import Callable
from pathlib import Path

import yaml

from resume_builder.infra.pdf import PdfRenderResult
from resume_builder.infra.pipeline import build_resume
from resume_builder.infra.scaffold import create_project_scaffold


def test_compaction_progression_stops_when_reaching_two_pages(
    tmp_path: Path,
    sample_payload: dict[str, object],
    profile_pdf_renderer: Callable[[dict[str, int]], Callable[[Path, Path], PdfRenderResult]],
) -> None:
    create_project_scaffold(tmp_path)

    data_path = tmp_path / "data" / "resume.yaml"
    with data_path.open("w", encoding="utf-8") as handle:
        yaml.safe_dump(sample_payload, handle, allow_unicode=True, sort_keys=False)

    renderer = profile_pdf_renderer({"padrao": 4, "compacto_1": 3, "compacto_2": 2})

    result = build_resume(
        input_yaml=data_path,
        template_html=tmp_path / "templates" / "resume.html",
        template_css=tmp_path / "templates" / "resume.css",
        dist_dir=tmp_path / "dist",
        render_pdf_fn=renderer,
    )

    assert result.pdf_path is not None and result.pdf_path.exists()
    assert len(result.attempts) == 3
    assert result.attempts[0].profile == "padrao"
    assert result.attempts[1].profile == "compacto_1"
    assert result.attempts[2].profile == "compacto_2"
    assert result.attempts[2].pages == 2
