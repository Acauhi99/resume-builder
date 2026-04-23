from __future__ import annotations

from pathlib import Path

import typer

from resume_builder.domain.compaction import CompactionProfile, default_profiles
from resume_builder.infra.io_ops import ensure_dir
from resume_builder.infra.pdf import PdfRenderError, render_pdf_with_fallback
from resume_builder.infra.pipeline import (
    build_resume,
    build_score_report,
    load_resume,
    persist_score_outputs,
    render_html_only,
)
from resume_builder.infra.scaffold import create_project_scaffold

app = typer.Typer(help="Gerador local de curriculo com score deterministico e exportacao PDF.")


def _profile_by_name(name: str) -> CompactionProfile:
    for profile in default_profiles():
        if profile.name == name:
            return profile
    available = ", ".join(p.name for p in default_profiles())
    raise typer.BadParameter(f"Perfil invalido. Opcoes: {available}")


@app.command("init")
def init_cmd(
    base_dir: Path = typer.Option(Path("."), help="Diretorio base do projeto."),
    force: bool = typer.Option(False, help="Sobrescrever arquivos existentes."),
) -> None:
    result = create_project_scaffold(base_dir.resolve(), force=force)
    for path in result.created:
        typer.echo(f"[created] {path}")
    for path in result.skipped:
        typer.echo(f"[skipped] {path}")


@app.command("score")
def score_cmd(
    input_yaml: Path = typer.Option(Path("data/resume.yaml"), help="Arquivo de entrada YAML."),
    dist_dir: Path = typer.Option(Path("dist"), help="Diretorio de saida para score."),
    target_score: float = typer.Option(90.0, help="Meta de score (0-100)."),
    language: str = typer.Option("pt-BR", help="Idioma para relatorio."),
) -> None:
    try:
        resume = load_resume(input_yaml)
        score = build_score_report(resume, target_score=target_score, language=language)
        score_json, score_md = persist_score_outputs(score, dist_dir=dist_dir)
    except Exception as exc:
        typer.echo(f"Erro ao calcular score: {exc}")
        raise typer.Exit(code=1) from exc

    typer.echo(f"Score: {score.pontuacao_total}/100 (meta={score.meta})")
    typer.echo(f"JSON: {score_json}")
    typer.echo(f"Markdown: {score_md}")


@app.command("render-html")
def render_html_cmd(
    input_yaml: Path = typer.Option(Path("data/resume.yaml"), help="Arquivo de entrada YAML."),
    template_html: Path = typer.Option(Path("templates/resume.html"), help="Template HTML."),
    template_css: Path = typer.Option(Path("templates/resume.css"), help="CSS de impressao."),
    output_html: Path = typer.Option(Path("dist/resume.html"), help="Arquivo HTML de saida."),
    profile: str = typer.Option("padrao", help="Perfil de compactacao."),
    target_score: float = typer.Option(90.0, help="Meta de score (0-100)."),
    language: str = typer.Option("pt-BR", help="Idioma para relatorio."),
) -> None:
    try:
        profile_obj = _profile_by_name(profile)
        out_path = render_html_only(
            input_yaml=input_yaml,
            template_html=template_html,
            template_css=template_css,
            output_html=output_html,
            target_score=target_score,
            language=language,
            profile=profile_obj,
        )
    except Exception as exc:
        typer.echo(f"Erro ao renderizar HTML: {exc}")
        raise typer.Exit(code=1) from exc

    typer.echo(f"HTML gerado: {out_path}")


@app.command("render-pdf")
def render_pdf_cmd(
    input_html: Path = typer.Option(Path("dist/resume.html"), help="Arquivo HTML de entrada."),
    output_pdf: Path = typer.Option(Path("dist/resume.pdf"), help="PDF de saida."),
) -> None:
    if not input_html.exists():
        typer.echo(f"Arquivo HTML nao encontrado: {input_html}")
        raise typer.Exit(code=1)

    ensure_dir(output_pdf.parent)

    try:
        result = render_pdf_with_fallback(input_html, output_pdf)
    except PdfRenderError as exc:
        typer.echo(f"Erro ao renderizar PDF: {exc}")
        raise typer.Exit(code=1) from exc

    typer.echo(
        f"PDF gerado: {result.output_path} | engine={result.engine} | paginas={result.pages}"
    )


@app.command("build")
def build_cmd(
    input_yaml: Path = typer.Option(Path("data/resume.yaml"), help="Arquivo de entrada YAML."),
    template_html: Path = typer.Option(Path("templates/resume.html"), help="Template HTML."),
    template_css: Path = typer.Option(Path("templates/resume.css"), help="CSS de impressao."),
    dist_dir: Path = typer.Option(Path("dist"), help="Diretorio de saida."),
    target_score: float = typer.Option(90.0, help="Meta de score (0-100)."),
    language: str = typer.Option("pt-BR", help="Idioma para relatorio."),
) -> None:
    try:
        result = build_resume(
            input_yaml=input_yaml,
            template_html=template_html,
            template_css=template_css,
            dist_dir=dist_dir,
            target_score=target_score,
            language=language,
        )
    except Exception as exc:
        typer.echo(f"Erro no build: {exc}")
        raise typer.Exit(code=1) from exc

    typer.echo(f"HTML: {result.html_path}")
    typer.echo(f"PDF: {result.pdf_path}")
    typer.echo(f"Score JSON: {result.score_json_path}")
    typer.echo(f"Score MD: {result.score_md_path}")

    typer.echo("Tentativas de compactacao:")
    for attempt in result.attempts:
        summary = (
            f"- {attempt.profile} | engine={attempt.engine} | "
            f"pages={attempt.pages} | error={attempt.error}"
        )
        typer.echo(summary)

    if result.score.atingiu_meta:
        typer.echo(f"Score final: {result.score.pontuacao_total}/100 (meta atingida)")
    else:
        summary = (
            f"Score final: {result.score.pontuacao_total}/100 "
            f"(abaixo da meta {result.score.meta}, PDF mantido)"
        )
        typer.echo(summary)


if __name__ == "__main__":
    app()
