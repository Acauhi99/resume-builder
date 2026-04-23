from __future__ import annotations

import re
from contextlib import suppress
from dataclasses import dataclass
from typing import Any

from rapidfuzz import fuzz

from resume_builder.domain.models import Recommendation, Resume, ScoreBreakdown, ScoreReport

_NUMBER_RE = re.compile(r"\b\d+(?:[.,]\d+)?\s?(?:%|x|h|m|k|mil|mi|M|anos?|meses?|dias?)?\b")
_SPACE_RE = re.compile(r"\s+")
_REPEAT_PUNCT_RE = re.compile(r"([!?.,;:])\1+")
_ALL_CAPS_RE = re.compile(r"\b[A-Z]{4,}\b")
_ACTION_VERBS = {
    "liderei",
    "conduzi",
    "implementei",
    "desenvolvi",
    "otimizei",
    "estruturei",
    "automatizei",
    "projetei",
    "criei",
    "reduzi",
    "aumentei",
    "melhorei",
    "escalei",
    "coordenei",
    "entreguei",
    "construi",
    "analisei",
}


@dataclass(frozen=True)
class ScoringContext:
    bullets: list[str]
    full_text: str


def _round(value: float) -> float:
    return round(max(0.0, min(100.0, value)), 1)


def _clamp(value: float, low: float, high: float) -> float:
    return max(low, min(high, value))


def _collect_context(resume: Resume) -> ScoringContext:
    bullets: list[str] = []
    blocks: list[str] = [resume.resumo]

    for exp in resume.experiencias:
        blocks.extend([exp.empresa, exp.cargo, exp.resumo or ""])
        bullets.extend(exp.bullets)

    for proj in resume.projetos:
        blocks.extend([proj.nome, proj.resumo])
        bullets.extend(proj.bullets)

    for edu in resume.educacao:
        blocks.extend([edu.instituicao, edu.curso, edu.detalhes or ""])

    blocks.extend(resume.skills)
    blocks.extend([b for b in bullets if b])

    full_text = "\n".join(blocks).strip()
    return ScoringContext(bullets=[b for b in bullets if b], full_text=full_text)


def _score_completude(resume: Resume) -> tuple[float, list[Recommendation]]:
    score = 0.0
    recommendations: list[Recommendation] = []

    contact_fields = [resume.contato.nome, resume.contato.titulo, resume.contato.email]
    contact_ok = sum(1 for field in contact_fields if field)
    score += (contact_ok / 3.0) * 8.0

    if resume.contato.linkedin or resume.contato.github or resume.contato.website:
        score += 2.0
    else:
        recommendations.append(
            Recommendation(
                prioridade="alta",
                mensagem="Adicione pelo menos um link profissional (LinkedIn, GitHub ou website).",
            )
        )

    section_rules: list[tuple[bool, float, str]] = [
        (bool(resume.resumo), 4.0, "Inclua um resumo profissional objetivo de 3 a 5 linhas."),
        (len(resume.experiencias) > 0, 5.0, "Adicione experiencias profissionais relevantes."),
        (len(resume.educacao) > 0, 3.0, "Adicione pelo menos uma entrada de educacao."),
        (len(resume.skills) > 0, 3.0, "Inclua uma secao de skills com tecnologias-chave."),
        (len(resume.projetos) > 0, 3.0, "Inclua pelo menos um projeto com contexto e impacto."),
    ]

    for ok, points, suggestion in section_rules:
        if ok:
            score += points
        else:
            recommendations.append(Recommendation(prioridade="alta", mensagem=suggestion))

    return _clamp(score, 0.0, 25.0), recommendations


def _starts_with_action_verb(text: str) -> bool:
    parts = text.strip().split()
    if not parts:
        return False
    first = re.sub(r"[^a-zA-ZA-Za-z]", "", parts[0]).casefold()
    return first in _ACTION_VERBS


def _score_impacto(context: ScoringContext) -> tuple[float, list[Recommendation]]:
    bullets = context.bullets
    if not bullets:
        return (
            0.0,
            [
                Recommendation(
                    prioridade="alta",
                    mensagem="Adicione bullets de impacto em experiencias e projetos.",
                )
            ],
        )

    quantified = sum(1 for bullet in bullets if _NUMBER_RE.search(bullet))
    action_verb = sum(1 for bullet in bullets if _starts_with_action_verb(bullet))

    quantified_ratio = quantified / len(bullets)
    action_ratio = action_verb / len(bullets)

    quantified_points = 15.0 * _clamp(quantified_ratio / 0.60, 0.0, 1.0)
    action_points = 10.0 * _clamp(action_ratio / 0.70, 0.0, 1.0)

    recs: list[Recommendation] = []
    if quantified_ratio < 0.45:
        recs.append(
            Recommendation(
                prioridade="alta",
                mensagem="Quantifique mais resultados com numeros, percentuais e escalas.",
            )
        )
    if action_ratio < 0.50:
        recs.append(
            Recommendation(
                prioridade="media",
                mensagem="Comece mais bullets com verbos de acao orientados a resultado.",
            )
        )

    return _clamp(quantified_points + action_points, 0.0, 25.0), recs


def _fallback_readability_score(text: str) -> float:
    sentences = [s for s in re.split(r"[.!?]+", text) if s.strip()]
    words = [w for w in re.split(r"\s+", text) if w.strip()]
    if not sentences or not words:
        return 0.0
    avg_words = len(words) / len(sentences)
    if avg_words <= 22:
        return 10.0
    penalty = min(10.0, (avg_words - 22) * 0.45)
    return max(0.0, 10.0 - penalty)


def _readability_score(text: str) -> float:
    try:
        import textstat

        with suppress(Exception):
            textstat.set_lang("pt")

        flesch = float(textstat.flesch_reading_ease(text))
        # Mapeia faixa util de legibilidade para 0-10.
        normalized = ((flesch - 20.0) / (70.0 - 20.0)) * 10.0
        return _clamp(normalized, 0.0, 10.0)
    except Exception:
        return _fallback_readability_score(text)


def _score_clareza(context: ScoringContext) -> tuple[float, list[Recommendation]]:
    bullets = context.bullets
    if not bullets:
        return 5.0, []

    words_per_bullet: list[int] = []
    for bullet in bullets:
        words = [w for w in bullet.strip().split() if w]
        words_per_bullet.append(len(words))

    in_range = sum(1 for count in words_per_bullet if 8 <= count <= 28)
    ratio = in_range / len(words_per_bullet)

    bullet_points = 10.0 * _clamp(ratio / 0.8, 0.0, 1.0)
    readability_points = _readability_score(context.full_text)

    recs: list[Recommendation] = []
    if ratio < 0.65:
        recs.append(
            Recommendation(
                prioridade="media",
                mensagem="Ajuste o tamanho dos bullets para entre 8 e 28 palavras.",
            )
        )
    if readability_points < 5.0:
        recs.append(
            Recommendation(
                prioridade="media",
                mensagem="Simplifique frases longas para melhorar clareza e leitura rapida.",
            )
        )

    return _clamp(bullet_points + readability_points, 0.0, 20.0), recs


def _parse_year_month(value: str | None) -> tuple[int, int] | None:
    if not value:
        return None
    match = re.match(r"^(\d{4})(?:[-/](\d{1,2}))?$", value.strip())
    if not match:
        return None
    year = int(match.group(1))
    month = int(match.group(2) or 1)
    return (year, month)


def _score_consistencia(
    resume: Resume, context: ScoringContext
) -> tuple[float, list[Recommendation]]:
    bullets = context.bullets
    recs: list[Recommendation] = []

    dup_score = 8.0
    if bullets:
        normalized: list[str] = []
        for bullet in bullets:
            line = re.sub(r"[^\w\s]", "", bullet.casefold())
            line = _SPACE_RE.sub(" ", line).strip()
            normalized.append(line)

        unique_count = 0
        for idx, item in enumerate(normalized):
            max_sim = 0.0
            for prev in normalized[:idx]:
                max_sim = max(max_sim, fuzz.ratio(item, prev))
            if max_sim < 92:
                unique_count += 1

        unique_ratio = unique_count / len(normalized)
        dup_score = 8.0 * _clamp(unique_ratio, 0.0, 1.0)
        if unique_ratio < 0.8:
            recs.append(
                Recommendation(
                    prioridade="media",
                    mensagem="Remova repeticoes e bullets semanticamente parecidos.",
                )
            )

    date_score = 5.0
    invalid_dates = 0
    for exp in resume.experiencias:
        start = _parse_year_month(exp.inicio)
        end = None if exp.atual else _parse_year_month(exp.fim)
        if start and end and end < start:
            invalid_dates += 1

    for edu in resume.educacao:
        start = _parse_year_month(edu.inicio)
        end = _parse_year_month(edu.fim)
        if start and end and end < start:
            invalid_dates += 1

    if invalid_dates > 0:
        date_score = max(0.0, date_score - (2.5 * invalid_dates))
        recs.append(
            Recommendation(
                prioridade="alta",
                mensagem="Revise datas: foram detectadas entradas com fim anterior ao inicio.",
            )
        )

    punct_score = 2.0
    if bullets:
        punctuated = sum(1 for bullet in bullets if bullet.strip().endswith("."))
        punct_ratio = max(punctuated / len(bullets), 1.0 - (punctuated / len(bullets)))
        punct_score = 2.0 * punct_ratio
        if punct_ratio < 0.75:
            recs.append(
                Recommendation(
                    prioridade="baixa",
                    mensagem=(
                        "Padronize pontuacao final dos bullets (todos com ponto ou todos sem)."
                    ),
                )
            )

    return _clamp(dup_score + date_score + punct_score, 0.0, 15.0), recs


def _score_higiene(context: ScoringContext) -> tuple[float, list[Recommendation]]:
    text = context.full_text
    issues = 0
    recs: list[Recommendation] = []

    if "  " in text:
        issues += 1
    if _REPEAT_PUNCT_RE.search(text):
        issues += 1
    if _ALL_CAPS_RE.search(text):
        issues += 1

    if issues > 0:
        recs.append(
            Recommendation(
                prioridade="media",
                mensagem=(
                    "Revise higiene textual: espacos, caixa alta excessiva e pontuacao repetida."
                ),
            )
        )

    score = max(0.0, 15.0 - (issues * 4.0))
    return _clamp(score, 0.0, 15.0), recs


def _sort_recommendations(recommendations: list[Recommendation]) -> list[Recommendation]:
    priority_order = {"alta": 0, "media": 1, "baixa": 2}
    dedupe: dict[tuple[str, str], Recommendation] = {}

    for rec in recommendations:
        key = (rec.prioridade, rec.mensagem)
        dedupe[key] = rec

    ordered = sorted(
        dedupe.values(),
        key=lambda rec: (priority_order.get(rec.prioridade, 9), rec.mensagem.casefold()),
    )
    return ordered


def score_resume(
    resume: Resume, *, target_score: float = 90.0, language: str = "pt-BR"
) -> ScoreReport:
    context = _collect_context(resume)

    completude, rec_a = _score_completude(resume)
    impacto, rec_b = _score_impacto(context)
    clareza, rec_c = _score_clareza(context)
    consistencia, rec_d = _score_consistencia(resume, context)
    higiene, rec_e = _score_higiene(context)

    total = completude + impacto + clareza + consistencia + higiene
    total = _clamp(total, 0.0, 100.0)

    breakdown = ScoreBreakdown(
        completude_ats=_round(completude),
        impacto_quantificacao=_round(impacto),
        clareza=_round(clareza),
        consistencia=_round(consistencia),
        higiene_textual=_round(higiene),
    )

    recommendations = _sort_recommendations(rec_a + rec_b + rec_c + rec_d + rec_e)

    return ScoreReport(
        idioma=language,
        pontuacao_total=_round(total),
        meta=_round(target_score),
        atingiu_meta=total >= target_score,
        breakdown=breakdown,
        recomendacoes=recommendations,
    )


def report_to_dict(report: ScoreReport) -> dict[str, Any]:
    return report.model_dump(mode="json")
