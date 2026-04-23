from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from resume_builder.infra.io_ops import ensure_dir, write_text

SAMPLE_YAML = """contato:
  nome: Ana Silva
  titulo: Engenheira de Software
  email: ana.silva@email.com
  telefone: +55 11 90000-0000
  localizacao: São Paulo, SP
  linkedin: https://linkedin.com/in/ana-silva
  github: https://github.com/ana-silva

resumo: >
  Engenheira de software com foco em backend e produtos digitais,
  com histórico de entrega de features críticas e melhoria de performance.

experiencias:
  - empresa: Inova Tech
    cargo: Software Engineer
    localizacao: São Paulo, SP
    inicio: "2022-03"
    fim: "2024-12"
    bullets:
      - Implementei pipeline de dados que reduziu o tempo de processamento em 38%.
      - Liderei migração de serviços para arquitetura orientada a eventos.
      - Desenvolvi testes automatizados elevando cobertura de 61% para 82%.
    tecnologias: [Python, FastAPI, PostgreSQL, Docker]

educacao:
  - instituicao: Universidade Federal X
    curso: Bacharelado em Ciência da Computação
    inicio: "2017"
    fim: "2021"

skills:
  - Python
  - FastAPI
  - SQL
  - Arquitetura de Software
  - CI/CD

projetos:
  - nome: Plataforma de Relatórios Operacionais
    resumo: Produto interno para monitoramento de indicadores de negócio em tempo real.
    bullets:
      - Construí APIs e jobs que processam mais de 2 milhões de eventos por dia.
      - Reduzi custo de infraestrutura em 22% com tuning de consultas e cache.
    link: https://github.com/ana-silva/projeto-relatorios
    tecnologias: [Python, Redis, PostgreSQL]

certificacoes:
  - nome: AWS Cloud Practitioner
    emissor: Amazon Web Services
    ano: "2023"

idiomas:
  - idioma: Português
    nivel: Nativo
  - idioma: Inglês
    nivel: Avançado
"""

SAMPLE_TEMPLATE = """<!DOCTYPE html>
<html lang="pt-BR">
  <head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0" />
    <title>Currículo - {{ resume.contato.nome }}</title>
    <style>
      :root {
        --body-font-pt: {{ css_tokens.body_font_pt }}pt;
        --heading-font-pt: {{ css_tokens.heading_font_pt }}pt;
        --line-height: {{ css_tokens.line_height }};
      }
    </style>
    <style>{{ css }}</style>
  </head>
  <body>
    <div class="sheet">
      <header class="topbar">
        <div class="identity">
          <h1>{{ resume.contato.nome }}</h1>
          <p class="subtitle">{{ resume.contato.titulo }}</p>
        </div>

        <ul class="contact" aria-label="Contato">
          <li><strong>Email</strong> <a href="mailto:{{ resume.contato.email }}">{{ resume.contato.email }}</a></li>
          {% if resume.contato.telefone %}<li><strong>Tel</strong> {{ resume.contato.telefone }}</li>{% endif %}
          {% if resume.contato.localizacao %}<li><strong>Local</strong> {{ resume.contato.localizacao }}</li>{% endif %}
          {% if resume.contato.linkedin %}<li><a href="{{ resume.contato.linkedin }}">LinkedIn</a></li>{% endif %}
          {% if resume.contato.github %}<li><a href="{{ resume.contato.github }}">GitHub</a></li>{% endif %}
          {% if resume.contato.website %}<li><a href="{{ resume.contato.website }}">Website</a></li>{% endif %}
        </ul>
      </header>

      <div class="layout">
        <main class="content">
          <section aria-labelledby="sumario">
            <h2 id="sumario" class="label">Resumo</h2>
            <p class="summary">{{ resume.resumo }}</p>
          </section>

          {% if resume.experiencias %}
          <section aria-labelledby="experiencia">
            <h2 id="experiencia" class="label">Experiência</h2>

            {% for exp in resume.experiencias %}
            <article class="entry">
              <div class="entry-head">
                <h3>{{ exp.cargo }}</h3>
                <p class="period">{{ exp.inicio }} - {% if exp.atual %}Presente{% else %}{{ exp.fim }}{% endif %}</p>
              </div>

              <p class="company-line">
                <span class="company">{{ exp.empresa }}</span>
                {% if exp.localizacao %}<span class="location">{{ exp.localizacao }}</span>{% endif %}
              </p>

              {% if exp.resumo %}<p class="entry-resume">{{ exp.resumo }}</p>{% endif %}

              {% if exp.bullets %}
              <ul class="dash-list">
                {% for bullet in exp.bullets %}
                <li>{{ bullet }}</li>
                {% endfor %}
              </ul>
              {% endif %}

              {% if exp.tecnologias %}
              <div class="chips">
                {% for tech in exp.tecnologias %}
                <span class="chip">{{ tech }}</span>
                {% endfor %}
              </div>
              {% endif %}
            </article>
            {% endfor %}
          </section>
          {% endif %}

          {% if resume.projetos %}
          <section aria-labelledby="projetos">
            <h2 id="projetos" class="label">Projetos</h2>

            {% for projeto in resume.projetos %}
            <article class="entry entry-project">
              <p class="project-line">
                <span class="project-name">{{ projeto.nome }}</span>
                {% if projeto.link %}<a href="{{ projeto.link }}" class="project-link">↗ link</a>{% endif %}
              </p>

              <p class="project-summary">{{ projeto.resumo }}</p>

              {% if projeto.bullets %}
              <ul class="dash-list">
                {% for bullet in projeto.bullets %}
                <li>{{ bullet }}</li>
                {% endfor %}
              </ul>
              {% endif %}

              {% if projeto.tecnologias %}
              <div class="chips">
                {% for tech in projeto.tecnologias %}
                <span class="chip">{{ tech }}</span>
                {% endfor %}
              </div>
              {% endif %}
            </article>
            {% endfor %}
          </section>
          {% endif %}
        </main>

        <aside class="sidebar">
          {% if resume.skills %}
          <section aria-labelledby="skills">
            <h2 id="skills" class="label">Habilidades</h2>
            <div class="skill-box">
              <p class="group-title">Stack</p>
              <div class="chips">
                {% for skill in resume.skills %}
                <span class="chip">{{ skill }}</span>
                {% endfor %}
              </div>
            </div>
          </section>
          {% endif %}

          {% if resume.educacao %}
          <section aria-labelledby="educacao">
            <h2 id="educacao" class="label">Educação</h2>
            {% for edu in resume.educacao %}
            <article class="edu-item">
              <p class="edu-course">{{ edu.curso }}</p>
              <p class="edu-inst">{{ edu.instituicao }}</p>
              <p class="edu-period">{{ edu.inicio }} - {{ edu.fim or 'Atual' }}</p>
              {% if edu.detalhes %}<p class="edu-details">{{ edu.detalhes }}</p>{% endif %}
            </article>
            {% endfor %}
          </section>
          {% endif %}

          {% if resume.certificacoes %}
          <section aria-labelledby="certs">
            <h2 id="certs" class="label">Certificações</h2>
            {% for cert in resume.certificacoes %}
            <article class="edu-item">
              <p class="edu-course">
                {% if cert.link %}<a href="{{ cert.link }}" class="cert-link">{{ cert.nome }}</a>{% else %}{{ cert.nome }}{% endif %}
              </p>
              <p class="edu-inst">{{ cert.emissor }}</p>
              {% if cert.ano %}<p class="edu-period">{{ cert.ano }}</p>{% endif %}
            </article>
            {% endfor %}
          </section>
          {% endif %}

          {% if resume.idiomas %}
          <section aria-labelledby="idiomas">
            <h2 id="idiomas" class="label">Idiomas</h2>
            {% for lang in resume.idiomas %}
            <div class="language-row">
              <span class="language">{{ lang.idioma }}</span>
              <span class="level">{{ lang.nivel }}</span>
            </div>
            {% endfor %}
          </section>
          {% endif %}
        </aside>
      </div>
    </div>
  </body>
</html>"""

SAMPLE_CSS = """@page {
  size: A4;
  margin: 12mm;
}

:root {
  --bg: #f6f4ef;
  --surface: #ffffff;
  --ink: #151515;
  --muted: #66635d;
  --accent: #1f4266;
  --accent-soft: #315a83;
  --line: #ded8ce;
  --pill: #ece7dd;

  --font-title: "Noto Serif", Georgia, serif;
  --font-body: "Lato", "Ubuntu Sans", "Segoe UI", sans-serif;

  --radius: 7px;
}

*,
*::before,
*::after {
  box-sizing: border-box;
}

html,
body {
  margin: 0;
  padding: 0;
}

body {
  background: var(--bg);
  color: var(--ink);
  font-family: var(--font-body);
  font-size: var(--body-font-pt);
  font-weight: 300;
  line-height: var(--line-height);
  display: flex;
  justify-content: center;
  padding: 1.1rem;
}

.sheet {
  width: 100%;
  max-width: 920px;
  background: var(--surface);
  border: 1px solid #ebe5da;
  border-radius: var(--radius);
  overflow: hidden;
  box-shadow: 0 4px 32px rgb(0 0 0 / 7%);
}

.topbar {
  padding: 2rem 2.1rem 1.5rem;
  border-bottom: 1px solid var(--line);
  display: grid;
  grid-template-columns: 1fr auto;
  gap: 1.4rem;
  align-items: start;
}

.identity h1 {
  margin: 0;
  font-family: var(--font-title);
  font-size: calc(var(--heading-font-pt) * 2.9);
  font-weight: 400;
  line-height: 1.03;
  letter-spacing: -0.35px;
  color: #101010;
}

.subtitle {
  margin: 0.26rem 0 0;
  font-family: var(--font-title);
  font-style: italic;
  font-weight: 400;
  font-size: calc(var(--body-font-pt) * 1.17);
  color: var(--accent-soft);
  letter-spacing: 0.2px;
}

.contact {
  margin: 0;
  padding: 0;
  list-style: none;
  display: flex;
  flex-direction: column;
  align-items: flex-end;
  gap: 0.24rem;
}

.contact li {
  color: var(--muted);
  font-weight: 400;
  font-size: calc(var(--body-font-pt) * 0.77);
}

.contact strong {
  color: var(--ink);
  font-weight: 600;
}

.contact a {
  color: var(--accent);
  text-decoration: none;
  font-weight: 600;
}

.layout {
  display: grid;
  grid-template-columns: minmax(0, 1fr) 248px;
}

.content {
  border-right: 1px solid var(--line);
  padding: 1.9rem 2.1rem;
}

.sidebar {
  padding: 1.9rem 1.45rem;
}

section + section {
  margin-top: 1.85rem;
}

.label {
  margin: 0 0 0.85rem;
  padding: 0 0 0.44rem;
  border-bottom: 1px solid var(--line);
  font-size: calc(var(--body-font-pt) * 0.62);
  letter-spacing: 2.3px;
  font-weight: 700;
  text-transform: uppercase;
  color: var(--accent);
}

.summary {
  margin: 0;
  max-width: 58ch;
  color: var(--muted);
  line-height: 1.74;
  font-size: calc(var(--body-font-pt) * 0.9);
}

.entry {
  break-inside: avoid;
  padding: 0.15rem 0 0.1rem;
}

.entry + .entry {
  margin-top: 1.4rem;
}

.entry-head {
  display: flex;
  justify-content: space-between;
  align-items: baseline;
  gap: 0.6rem;
  flex-wrap: wrap;
}

.entry-head h3 {
  margin: 0;
  font-family: var(--font-title);
  font-size: calc(var(--body-font-pt) * 1.2);
  line-height: 1.2;
  font-weight: 600;
}

.period {
  margin: 0;
  white-space: nowrap;
  color: var(--muted);
  font-size: calc(var(--body-font-pt) * 0.75);
}

.company-line {
  margin: 0.08rem 0 0;
}

.company {
  color: var(--accent);
  font-size: calc(var(--body-font-pt) * 0.84);
  font-weight: 600;
}

.location {
  margin-left: 0.4rem;
  color: var(--muted);
  font-size: calc(var(--body-font-pt) * 0.76);
}

.entry-resume {
  margin: 0.26rem 0 0;
  color: var(--muted);
  font-size: calc(var(--body-font-pt) * 0.83);
  line-height: 1.62;
}

.dash-list {
  margin: 0.58rem 0 0;
  padding: 0 0 0 1rem;
  list-style: none;
}

.dash-list li {
  position: relative;
  padding-left: 0.72rem;
  color: var(--muted);
  font-size: calc(var(--body-font-pt) * 0.84);
  line-height: 1.63;
}

.dash-list li::before {
  content: "-";
  position: absolute;
  left: 0;
  top: 0;
  color: var(--accent);
  font-weight: 700;
}

.project-line {
  margin: 0;
}

.project-name {
  color: var(--ink);
  font-size: calc(var(--body-font-pt) * 0.9);
  font-weight: 600;
}

.project-link {
  margin-left: 0.36rem;
  color: var(--accent);
  font-size: calc(var(--body-font-pt) * 0.74);
  font-weight: 600;
  text-decoration: none;
}

.project-summary {
  margin: 0.2rem 0 0;
  color: var(--muted);
  font-size: calc(var(--body-font-pt) * 0.83);
  line-height: 1.6;
}

.chips {
  display: flex;
  flex-wrap: wrap;
  gap: 0.3rem;
  margin-top: 0.62rem;
}

.chip {
  background: var(--pill);
  color: #1b1b1b;
  font-size: calc(var(--body-font-pt) * 0.7);
  font-weight: 600;
  border-radius: 999px;
  padding: 0.18rem 0.52rem;
  line-height: 1.2;
}

.skill-box {
  break-inside: avoid;
}

.group-title {
  margin: 0 0 0.42rem;
  color: var(--muted);
  font-size: calc(var(--body-font-pt) * 0.7);
  letter-spacing: 1.2px;
  font-weight: 700;
  text-transform: uppercase;
}

.edu-item {
  break-inside: avoid;
}

.edu-item + .edu-item {
  margin-top: 0.88rem;
}

.edu-course {
  margin: 0;
  color: var(--ink);
  font-size: calc(var(--body-font-pt) * 0.9);
  font-weight: 600;
}

.cert-link {
  color: inherit;
  text-decoration: none;
}

.cert-link:hover {
  color: var(--accent);
  text-decoration: underline;
}

.edu-inst {
  margin: 0.05rem 0 0;
  color: var(--accent);
  font-size: calc(var(--body-font-pt) * 0.8);
  font-weight: 500;
}

.edu-period {
  margin: 0.05rem 0 0;
  color: var(--muted);
  font-size: calc(var(--body-font-pt) * 0.75);
}

.edu-details {
  margin: 0.12rem 0 0;
  color: var(--muted);
  font-size: calc(var(--body-font-pt) * 0.74);
}

.language-row {
  display: flex;
  justify-content: space-between;
  gap: 0.5rem;
  margin-bottom: 0.28rem;
}

.language {
  color: var(--ink);
  font-size: calc(var(--body-font-pt) * 0.83);
  font-weight: 600;
}

.level {
  color: var(--muted);
  font-size: calc(var(--body-font-pt) * 0.76);
}

@media print {
  body {
    padding: 0;
    background: #fff;
    display: block;
  }

  .sheet {
    box-shadow: none;
    border-radius: 0;
    border-color: transparent;
  }
}

@media (max-width: 760px) {
  .topbar {
    grid-template-columns: 1fr;
  }

  .contact {
    align-items: flex-start;
  }

  .layout {
    grid-template-columns: 1fr;
  }

  .content {
    border-right: none;
    border-bottom: 1px solid var(--line);
    padding: 1.6rem 1.2rem;
  }

  .sidebar {
    padding: 1.6rem 1.2rem;
  }

  .topbar {
    padding: 1.7rem 1.2rem 1.3rem;
  }
}"""


@dataclass(frozen=True)
class InitResult:
    created: list[Path]
    skipped: list[Path]


def _write_if_needed(path: Path, content: str, *, force: bool) -> bool:
    if path.exists() and not force:
        return False
    write_text(path, content)
    return True


def create_project_scaffold(base_dir: Path, *, force: bool = False) -> InitResult:
    data_dir = base_dir / "data"
    template_dir = base_dir / "templates"
    ensure_dir(data_dir)
    ensure_dir(template_dir)

    targets = {
        data_dir / "resume.yaml": SAMPLE_YAML,
        template_dir / "resume.html": SAMPLE_TEMPLATE,
        template_dir / "resume.css": SAMPLE_CSS,
    }

    created: list[Path] = []
    skipped: list[Path] = []

    for path, content in targets.items():
        if _write_if_needed(path, content, force=force):
            created.append(path)
        else:
            skipped.append(path)

    return InitResult(created=created, skipped=skipped)
