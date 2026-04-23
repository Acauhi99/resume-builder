from __future__ import annotations

from resume_builder.domain.models import ScoreReport


def score_report_markdown(report: ScoreReport) -> str:
    status = "Atingiu" if report.atingiu_meta else "Abaixo"

    lines = [
        "# Relatorio de Score do Curriculo",
        "",
        f"- Idioma: `{report.idioma}`",
        f"- Pontuacao total: **{report.pontuacao_total:.1f}/100**",
        f"- Meta: **{report.meta:.1f}** ({status} da meta)",
        "",
        "## Breakdown",
        "",
        "| Criterio | Pontos |",
        "|---|---:|",
        f"| Completude ATS | {report.breakdown.completude_ats:.1f} / 25 |",
        f"| Impacto e quantificacao | {report.breakdown.impacto_quantificacao:.1f} / 25 |",
        f"| Clareza | {report.breakdown.clareza:.1f} / 20 |",
        f"| Consistencia | {report.breakdown.consistencia:.1f} / 15 |",
        f"| Higiene textual | {report.breakdown.higiene_textual:.1f} / 15 |",
        "",
        "## Recomendacoes priorizadas",
        "",
    ]

    if not report.recomendacoes:
        lines.append("- Nenhuma recomendacao critica. O curriculo esta consistente.")
    else:
        for rec in report.recomendacoes:
            lines.append(f"- **{rec.prioridade.upper()}**: {rec.mensagem}")

    lines.append("")
    return "\n".join(lines)
