from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path

from pydantic import ValidationError

from resume_builder.domain.compaction import CompactionProfile, apply_compaction, default_profiles
from resume_builder.domain.models import Resume, ScoreReport
from resume_builder.domain.normalize import normalize_resume
from resume_builder.domain.scoring import report_to_dict, score_resume
from resume_builder.infra.io_ops import ensure_dir, read_yaml, write_json, write_text
from resume_builder.infra.pdf import PdfRenderError, PdfRenderResult, render_pdf_with_fallback
from resume_builder.infra.reports import score_report_markdown
from resume_builder.infra.templating import render_resume_html


@dataclass(frozen=True)
class BuildAttempt:
    profile: str
    engine: str | None
    pages: int | None
    error: str | None


@dataclass(frozen=True)
class BuildResult:
    html_path: Path
    pdf_path: Path | None
    score_json_path: Path
    score_md_path: Path
    score: ScoreReport
    attempts: list[BuildAttempt]


RenderPdfFn = Callable[[Path, Path], PdfRenderResult]


def load_resume(input_yaml: Path) -> Resume:
    payload = read_yaml(input_yaml)
    try:
        parsed = Resume.model_validate(payload)
    except ValidationError as exc:
        raise ValueError(f"YAML invalido para schema de curriculo: {exc}") from exc
    return normalize_resume(parsed)


def build_score_report(
    resume: Resume,
    *,
    target_score: float,
    language: str = "pt-BR",
) -> ScoreReport:
    return score_resume(resume, target_score=target_score, language=language)


def persist_score_outputs(score: ScoreReport, *, dist_dir: Path) -> tuple[Path, Path]:
    ensure_dir(dist_dir)
    score_json = dist_dir / "score.json"
    score_md = dist_dir / "score.md"

    write_json(score_json, report_to_dict(score))
    write_text(score_md, score_report_markdown(score))
    return score_json, score_md


def _render_pdf(render_pdf_fn: RenderPdfFn, html_path: Path, output_pdf: Path) -> PdfRenderResult:
    return render_pdf_fn(html_path, output_pdf)


def build_resume(
    *,
    input_yaml: Path,
    template_html: Path,
    template_css: Path,
    dist_dir: Path,
    target_score: float = 90.0,
    language: str = "pt-BR",
    render_pdf_fn: RenderPdfFn = render_pdf_with_fallback,
    profiles: list[CompactionProfile] | None = None,
) -> BuildResult:
    ensure_dir(dist_dir)

    resume = load_resume(input_yaml)
    score = build_score_report(resume, target_score=target_score, language=language)
    score_json_path, score_md_path = persist_score_outputs(score, dist_dir=dist_dir)

    html_path = dist_dir / "resume.html"
    final_pdf = dist_dir / "resume.pdf"

    attempts: list[BuildAttempt] = []
    attempt_pdf_paths: list[Path] = []
    selected_pdf: Path | None = None

    profile_list = profiles or default_profiles()

    for profile in profile_list:
        compacted = apply_compaction(resume, profile)
        html = render_resume_html(
            resume=compacted,
            score=score,
            template_path=template_html,
            css_path=template_css,
            profile=profile,
        )
        write_text(html_path, html)

        attempt_pdf = dist_dir / f"resume.{profile.name}.pdf"
        attempt_pdf_paths.append(attempt_pdf)

        try:
            render_result = _render_pdf(render_pdf_fn, html_path, attempt_pdf)
        except PdfRenderError as exc:
            attempts.append(
                BuildAttempt(
                    profile=profile.name,
                    engine=None,
                    pages=None,
                    error=str(exc),
                )
            )
            continue

        attempts.append(
            BuildAttempt(
                profile=profile.name,
                engine=render_result.engine,
                pages=render_result.pages,
                error=None,
            )
        )

        if render_result.pages <= 2:
            final_pdf.write_bytes(attempt_pdf.read_bytes())
            selected_pdf = final_pdf
            break

    if selected_pdf is None:
        rendered = [a for a in attempts if a.pages is not None]
        if rendered:
            last = rendered[-1]
            overflow_path = dist_dir / "resume_overflow.pdf"
            source = dist_dir / f"resume.{last.profile}.pdf"
            if source.exists():
                overflow_path.write_bytes(source.read_bytes())
        attempt_text = ", ".join(
            f"{a.profile}: pages={a.pages} engine={a.engine} error={a.error}" for a in attempts
        )
        raise RuntimeError(
            "Nao foi possivel gerar curriculo com no maximo 2 paginas. "
            f"Tentativas: {attempt_text or 'nenhuma'}"
        )

    for temp_pdf in attempt_pdf_paths:
        if temp_pdf.exists():
            temp_pdf.unlink()

    return BuildResult(
        html_path=html_path,
        pdf_path=selected_pdf,
        score_json_path=score_json_path,
        score_md_path=score_md_path,
        score=score,
        attempts=attempts,
    )


def render_html_only(
    *,
    input_yaml: Path,
    template_html: Path,
    template_css: Path,
    output_html: Path,
    target_score: float,
    language: str,
    profile: CompactionProfile | None = None,
) -> Path:
    resume = load_resume(input_yaml)
    score = build_score_report(resume, target_score=target_score, language=language)
    compacted = apply_compaction(resume, profile or default_profiles()[0])
    html = render_resume_html(
        resume=compacted,
        score=score,
        template_path=template_html,
        css_path=template_css,
        profile=profile or default_profiles()[0],
    )
    write_text(output_html, html)
    return output_html
