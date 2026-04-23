from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field, model_validator


class Contato(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    nome: str = Field(min_length=2)
    titulo: str = Field(min_length=2)
    email: str = Field(min_length=5)
    telefone: str | None = None
    localizacao: str | None = None
    linkedin: str | None = None
    github: str | None = None
    website: str | None = None


class Experiencia(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    empresa: str = Field(min_length=2)
    cargo: str = Field(min_length=2)
    localizacao: str | None = None
    inicio: str = Field(min_length=4)
    fim: str | None = None
    atual: bool = False
    resumo: str | None = None
    bullets: list[str] = Field(default_factory=list)
    tecnologias: list[str] = Field(default_factory=list)

    @model_validator(mode="after")
    def ensure_end_or_current(self) -> Experiencia:
        if not self.atual and not self.fim:
            raise ValueError("Experiencia precisa de fim quando atual=false")
        return self


class Educacao(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    instituicao: str = Field(min_length=2)
    curso: str = Field(min_length=2)
    inicio: str = Field(min_length=4)
    fim: str | None = None
    detalhes: str | None = None


class Projeto(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    nome: str = Field(min_length=2)
    resumo: str = Field(min_length=5)
    bullets: list[str] = Field(default_factory=list)
    link: str | None = None
    tecnologias: list[str] = Field(default_factory=list)


class Certificacao(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    nome: str = Field(min_length=2)
    emissor: str = Field(min_length=2)
    ano: str | None = None


class Idioma(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    idioma: str = Field(min_length=2)
    nivel: str = Field(min_length=2)


class Resume(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    contato: Contato
    resumo: str = Field(min_length=8)
    experiencias: list[Experiencia] = Field(default_factory=list)
    educacao: list[Educacao] = Field(default_factory=list)
    skills: list[str] = Field(default_factory=list)
    projetos: list[Projeto] = Field(default_factory=list)
    certificacoes: list[Certificacao] = Field(default_factory=list)
    idiomas: list[Idioma] = Field(default_factory=list)


class ScoreBreakdown(BaseModel):
    model_config = ConfigDict(extra="forbid")

    completude_ats: float
    impacto_quantificacao: float
    clareza: float
    consistencia: float
    higiene_textual: float


class Recommendation(BaseModel):
    model_config = ConfigDict(extra="forbid")

    prioridade: str
    mensagem: str


class ScoreReport(BaseModel):
    model_config = ConfigDict(extra="forbid")

    idioma: str = "pt-BR"
    pontuacao_total: float
    meta: float
    atingiu_meta: bool
    breakdown: ScoreBreakdown
    recomendacoes: list[Recommendation]
