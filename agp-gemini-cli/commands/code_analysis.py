import os
import sys

import typer

# Añadir el directorio padre al path para poder importar la interfaz de Gemini
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from gemini_interface import generar_idea

code_analysis_app = typer.Typer(
    name="code-analysis", help="Herramientas de análisis de código con IA."
)


@code_analysis_app.command(name="analyze")
def analyze_code(
    file_path: str = typer.Argument(..., help="Ruta al archivo de código a analizar."),
    prompt_suffix: str = typer.Option(
        "",
        "--prompt-suffix",
        "-p",
        help="Sufijo para el prompt de la IA (ej. 'identifica errores', 'sugiere mejoras').",
    ),
):
    """
    Analiza un archivo de código fuente usando la IA de Gemini.
    """
    if not os.path.exists(file_path):
        typer.secho(f"Error: El archivo '{file_path}' no existe.", fg=typer.colors.RED)
        raise typer.Abort()

    typer.echo(f"Analizando código en: {file_path}...")
    try:
        with open(file_path, "r") as f:
            code_content = f.read()

        full_prompt = (
            f"Eres un asistente de IA experto en programación. Analiza el siguiente código fuente. "
            f"Proporciona un resumen de su funcionalidad, identifica posibles errores o malas prácticas, y sugiere mejoras. "
            f"Si el usuario proporciona un sufijo de prompt, incorpóralo en tu análisis. "
            f"\n\nCódigo:\n```\n{code_content}\n```\n\nAnálisis y Sugerencias: {prompt_suffix}"
        )

        typer.echo("🤖 Enviando código a Gemini para análisis...")
        analysis_result = generar_idea(full_prompt)

        typer.secho("\n--- ANÁLISIS DE CÓDIGO POR IA ---", fg=typer.colors.CYAN)
        typer.echo(analysis_result)
        typer.secho("----------------------------------", fg=typer.colors.CYAN)

    except Exception as e:
        typer.secho(
            f"Ha ocurrido un error inesperado durante el análisis: {e}",
            fg=typer.colors.RED,
        )
