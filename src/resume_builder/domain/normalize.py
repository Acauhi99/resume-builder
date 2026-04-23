from __future__ import annotations

import re
from collections.abc import Iterable

from resume_builder.domain.models import Educacao, Experiencia, Projeto, Resume

_SPACE_RE = re.compile(r"\s+")
_DATE_RE = re.compile(r"^(?P<year>\d{4})(?:[-/](?P<month>\d{1,2}))?$")

type IndexedExperience = tuple[int, Experiencia]
type IndexedEducation = tuple[int, Educacao]


def _clean_text(value: str | None) -> str | None:
    if value is None:
        return None
    cleaned = _SPACE_RE.sub(" ", value.strip())
    return cleaned or None


def _clean_list(values: Iterable[str]) -> list[str]:
    out: list[str] = []
    seen: set[str] = set()
    for value in values:
        cleaned = _clean_text(value)
        if not cleaned:
            continue
        key = cleaned.casefold()
        if key in seen:
            continue
        seen.add(key)
        out.append(cleaned)
    return out


def _date_key(date_value: str | None) -> tuple[int, int]:
    if not date_value:
        return (0, 0)
    match = _DATE_RE.match(date_value.strip())
    if not match:
        return (0, 0)
    year = int(match.group("year"))
    month = int(match.group("month") or 1)
    return (year, month)


def _normalize_experience(item: Experiencia) -> Experiencia:
    return item.model_copy(
        update={
            "empresa": _clean_text(item.empresa),
            "cargo": _clean_text(item.cargo),
            "localizacao": _clean_text(item.localizacao),
            "inicio": _clean_text(item.inicio),
            "fim": _clean_text(item.fim),
            "resumo": _clean_text(item.resumo),
            "bullets": _clean_list(item.bullets),
            "tecnologias": _clean_list(item.tecnologias),
        }
    )


def _normalize_education(item: Educacao) -> Educacao:
    return item.model_copy(
        update={
            "instituicao": _clean_text(item.instituicao),
            "curso": _clean_text(item.curso),
            "inicio": _clean_text(item.inicio),
            "fim": _clean_text(item.fim),
            "detalhes": _clean_text(item.detalhes),
        }
    )


def _normalize_project(item: Projeto) -> Projeto:
    return item.model_copy(
        update={
            "nome": _clean_text(item.nome),
            "resumo": _clean_text(item.resumo),
            "bullets": _clean_list(item.bullets),
            "tecnologias": _clean_list(item.tecnologias),
            "link": _clean_text(item.link),
        }
    )


def normalize_resume(resume: Resume) -> Resume:
    experiences = [_normalize_experience(e) for e in resume.experiencias]
    indexed_experiences: list[IndexedExperience] = list(enumerate(experiences))
    indexed_experiences.sort(
        key=lambda item: (
            1 if item[1].atual else 0,
            _date_key(item[1].inicio),
            -item[0],
        ),
        reverse=True,
    )

    education = [_normalize_education(e) for e in resume.educacao]
    indexed_education: list[IndexedEducation] = list(enumerate(education))
    indexed_education.sort(
        key=lambda item: (_date_key(item[1].fim or item[1].inicio), -item[0]),
        reverse=True,
    )

    projetos = [_normalize_project(p) for p in resume.projetos]

    return resume.model_copy(
        update={
            "resumo": _clean_text(resume.resumo),
            "skills": _clean_list(resume.skills),
            "experiencias": [item[1] for item in indexed_experiences],
            "educacao": [item[1] for item in indexed_education],
            "projetos": projetos,
            "certificacoes": [
                c.model_copy(
                    update={
                        "nome": _clean_text(c.nome),
                        "emissor": _clean_text(c.emissor),
                        "ano": _clean_text(c.ano),
                    }
                )
                for c in resume.certificacoes
            ],
            "idiomas": [
                i.model_copy(
                    update={
                        "idioma": _clean_text(i.idioma),
                        "nivel": _clean_text(i.nivel),
                    }
                )
                for i in resume.idiomas
            ],
        }
    )
