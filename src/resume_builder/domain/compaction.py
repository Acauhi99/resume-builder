from __future__ import annotations

from dataclasses import dataclass

from resume_builder.domain.models import Resume


@dataclass(frozen=True)
class CompactionProfile:
    name: str
    body_font_pt: float
    heading_font_pt: float
    line_height: float
    section_gap_rem: float
    item_gap_rem: float
    page_margin_mm: int
    max_experience_bullets: int
    max_project_bullets: int
    include_certifications: bool
    include_languages: bool
    summary_max_chars: int


def default_profiles() -> list[CompactionProfile]:
    return [
        CompactionProfile(
            name="padrao",
            body_font_pt=10.8,
            heading_font_pt=12.8,
            line_height=1.42,
            section_gap_rem=0.92,
            item_gap_rem=0.55,
            page_margin_mm=16,
            max_experience_bullets=5,
            max_project_bullets=4,
            include_certifications=True,
            include_languages=True,
            summary_max_chars=440,
        ),
        CompactionProfile(
            name="compacto_1",
            body_font_pt=10.4,
            heading_font_pt=12.2,
            line_height=1.35,
            section_gap_rem=0.82,
            item_gap_rem=0.50,
            page_margin_mm=14,
            max_experience_bullets=4,
            max_project_bullets=3,
            include_certifications=True,
            include_languages=True,
            summary_max_chars=390,
        ),
        CompactionProfile(
            name="compacto_2",
            body_font_pt=10.0,
            heading_font_pt=11.8,
            line_height=1.30,
            section_gap_rem=0.72,
            item_gap_rem=0.45,
            page_margin_mm=12,
            max_experience_bullets=4,
            max_project_bullets=2,
            include_certifications=False,
            include_languages=True,
            summary_max_chars=340,
        ),
        CompactionProfile(
            name="compacto_3",
            body_font_pt=9.6,
            heading_font_pt=11.4,
            line_height=1.25,
            section_gap_rem=0.64,
            item_gap_rem=0.40,
            page_margin_mm=10,
            max_experience_bullets=3,
            max_project_bullets=2,
            include_certifications=False,
            include_languages=False,
            summary_max_chars=290,
        ),
    ]


def _shorten(text: str, limit: int) -> str:
    if len(text) <= limit:
        return text
    trimmed = text[: max(0, limit - 3)].rstrip()
    return f"{trimmed}..."


def _limit_items(values: list[str], limit: int) -> list[str]:
    return values[: max(0, limit)]


def apply_compaction(resume: Resume, profile: CompactionProfile) -> Resume:
    return resume.model_copy(
        update={
            "resumo": _shorten(resume.resumo, profile.summary_max_chars),
            "experiencias": [
                item.model_copy(
                    update={"bullets": _limit_items(item.bullets, profile.max_experience_bullets)}
                )
                for item in resume.experiencias
            ],
            "projetos": [
                item.model_copy(
                    update={"bullets": _limit_items(item.bullets, profile.max_project_bullets)}
                )
                for item in resume.projetos
            ],
            "certificacoes": (resume.certificacoes if profile.include_certifications else []),
            "idiomas": resume.idiomas if profile.include_languages else [],
        }
    )
