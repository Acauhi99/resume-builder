from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path

from jinja2 import Environment, FileSystemLoader, StrictUndefined

from resume_builder.domain.compaction import CompactionProfile
from resume_builder.domain.models import Resume, ScoreReport


def _env_for(template_path: Path) -> Environment:
    return Environment(
        loader=FileSystemLoader(str(template_path.parent)),
        autoescape=True,
        trim_blocks=True,
        lstrip_blocks=True,
        undefined=StrictUndefined,
    )


def _css_tokens(profile: CompactionProfile) -> dict[str, str | float | int]:
    return {
        "body_font_pt": profile.body_font_pt,
        "heading_font_pt": profile.heading_font_pt,
        "line_height": profile.line_height,
        "section_gap_rem": profile.section_gap_rem,
        "item_gap_rem": profile.item_gap_rem,
        "page_margin_mm": profile.page_margin_mm,
    }


def render_resume_html(
    *,
    resume: Resume,
    score: ScoreReport,
    template_path: Path,
    css_path: Path,
    profile: CompactionProfile,
) -> str:
    env = _env_for(template_path)
    template = env.get_template(template_path.name)
    css_content = css_path.read_text(encoding="utf-8")

    return template.render(
        resume=resume.model_dump(mode="json"),
        score=score.model_dump(mode="json"),
        css=css_content,
        css_tokens=_css_tokens(profile),
        profile_name=profile.name,
        generated_at=datetime.now(UTC).strftime("%Y-%m-%d %H:%M UTC"),
    )
