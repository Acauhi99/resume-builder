# resume-builder

Gerador local de curriculo em Python + UV.

## Setup

```bash
uv sync --group dev
```

## Fluxo

1. YAML de entrada (`data/resume.yaml`)
2. Validacao e normalizacao
3. Score deterministico (ATS + clareza)
4. Render HTML (Jinja2)
5. Export PDF com WeasyPrint e fallback Playwright/Chrome

## Comandos

```bash
uv run resume init
uv run resume score
uv run resume render-html
uv run resume render-pdf
uv run resume build
```

## Qualidade de codigo

```bash
uv run ruff format src tests
uv run ruff check src tests
uv run mypy src tests
uv run python -m pytest -q
```

## Saidas

- `dist/resume.html`
- `dist/resume.pdf`
- `dist/score.json`
- `dist/score.md`
