from __future__ import annotations

from resume_builder.domain.models import Resume
from resume_builder.domain.normalize import normalize_resume
from resume_builder.domain.scoring import score_resume


def test_scoring_snapshot_is_stable(sample_payload: dict[str, object]) -> None:
    resume = normalize_resume(Resume.model_validate(sample_payload))
    report = score_resume(resume, target_score=90.0, language="pt-BR")

    assert report.model_dump() == {
        "idioma": "pt-BR",
        "pontuacao_total": 88.3,
        "meta": 90.0,
        "atingiu_meta": False,
        "breakdown": {
            "completude_ats": 25.0,
            "impacto_quantificacao": 25.0,
            "clareza": 8.3,
            "consistencia": 15.0,
            "higiene_textual": 15.0,
        },
        "recomendacoes": [
            {
                "prioridade": "media",
                "mensagem": "Simplifique frases longas para melhorar clareza e leitura rapida.",
            }
        ],
    }
