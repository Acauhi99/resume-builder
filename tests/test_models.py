from __future__ import annotations

import pytest
from pydantic import ValidationError

from resume_builder.domain.models import Resume


def test_resume_schema_accepts_valid_payload(sample_payload: dict[str, object]) -> None:
    resume = Resume.model_validate(sample_payload)
    assert resume.contato.nome == "Ana Silva"
    assert len(resume.experiencias) == 1


def test_resume_schema_rejects_experience_without_end_when_not_current(
    sample_payload: dict[str, object],
) -> None:
    payload = dict(sample_payload)
    payload["experiencias"] = [
        {
            "empresa": "Empresa X",
            "cargo": "Software Engineer",
            "inicio": "2022-01",
            "atual": False,
            "bullets": ["Implementei testes em toda a stack."],
        }
    ]

    with pytest.raises(ValidationError):
        Resume.model_validate(payload)
