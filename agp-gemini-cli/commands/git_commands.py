import subprocess

import typer
from gemini_interface import generar_idea

git_app = typer.Typer(name="git", help="Comandos básicos de Git.")


def _run_git_command(command: list[str], cwd: str = None):
    """
    Ejecuta un comando Git y maneja la salida/errores.
    """
    try:
        result = subprocess.run(
            command, capture_output=True, text=True, check=True, cwd=cwd
        )
        typer.echo(result.stdout)
        if result.stderr:
            typer.secho(result.stderr, fg=typer.colors.YELLOW)
    except subprocess.CalledProcessError as e:
        typer.secho(f"Error al ejecutar Git: {e.stderr}", fg=typer.colors.RED)
    except FileNotFoundError:
        typer.secho(
            "Error: Git no encontrado. Asegúrate de que Git está instalado en tu sistema.",
            fg=typer.colors.RED,
        )


@git_app.command(name="init")
def git_init(
    path: str = typer.Argument(".", help="Ruta donde inicializar el repositorio."),
):
    """
    Inicializa un nuevo repositorio Git.
    """
    typer.echo(f"Inicializando repositorio Git en: {path}")
    _run_git_command(["git", "init"], cwd=path)


@git_app.command(name="clone")
def git_clone(
    repo_url: str = typer.Argument(..., help="URL del repositorio a clonar."),
    path: str = typer.Argument(None, help="Directorio donde clonar el repositorio."),
):
    """
    Clona un repositorio Git.
    """
    command = ["git", "clone", repo_url]
    if path:
        command.append(path)
    typer.echo(f"Clonando repositorio: {repo_url}")
    _run_git_command(command)


@git_app.command(name="add")
def git_add(
    files: list[str] = typer.Argument(
        ..., help="Archivos a añadir (ej. . para todos)."
    ),
):
    """
    Añade cambios al área de preparación.
    """
    typer.echo(f"Añadiendo archivos: {files}")
    _run_git_command(["git", "add"] + files)


@git_app.command(name="commit")
def git_commit(message: str = typer.Option(..., "-m", help="Mensaje del commit.")):
    """
    Realiza un commit de los cambios preparados.
    """
    typer.echo(f"Realizando commit con mensaje: {message}")
    _run_git_command(["git", "commit", "-m", message])


@git_app.command(name="push")
def git_push(
    remote: str = typer.Argument("origin", help="Nombre del remoto."),
    branch: str = typer.Argument("main", help="Rama a empujar."),
):
    """
    Empuja los cambios al repositorio remoto.
    """
    typer.echo(f"Empujando cambios a {remote}/{branch}")
    _run_git_command(["git", "push", remote, branch])


@git_app.command(name="pull")
def git_pull(
    remote: str = typer.Argument("origin", help="Nombre del remoto."),
    branch: str = typer.Argument("main", help="Rama a traer."),
):
    """
    Trae y fusiona cambios del repositorio remoto.
    """
    typer.echo(f"Trayendo cambios de {remote}/{branch}")
    _run_git_command(["git", "pull", remote, branch])


@git_app.command(name="status")
def git_status():
    """
    Muestra el estado del repositorio.
    """
    typer.echo("Obteniendo estado de Git...")
    _run_git_command(["git", "status"])


@git_app.command(name="log")
def git_log(
    limit: int = typer.Option(5, "--limit", "-n", help="Número de commits a mostrar."),
):
    """
    Muestra el historial de commits.
    """
    typer.echo(f"Mostrando los últimos {limit} commits...")
    _run_git_command(["git", "log", f"-n{limit}"])


@git_app.command(name="branch")
def git_branch(
    name: str = typer.Argument(
        None,
        help="Nombre de la nueva rama a crear. Si no se especifica, lista las ramas existentes.",
    ),
):
    """
    Crea una nueva rama o lista las existentes.
    """
    if name:
        typer.echo(f"Creando rama: {name}")
        _run_git_command(["git", "branch", name])
    else:
        typer.echo("Listando ramas...")
        _run_git_command(["git", "branch"])


@git_app.command(name="checkout")
def git_checkout(
    branch_name: str = typer.Argument(..., help="Nombre de la rama a la que cambiar."),
):
    """
    Cambia a una rama existente.
    """
    typer.echo(f"Cambiando a la rama: {branch_name}")
    _run_git_command(["git", "checkout", branch_name])


@git_app.command(name="merge")
def git_merge(
    branch_name: str = typer.Argument(
        ..., help="Nombre de la rama a fusionar con la rama actual."
    ),
):
    """
    Fusiona la rama especificada con la rama actual.
    """
    typer.echo(f"Fusionando rama '{branch_name}' con la rama actual...")
    _run_git_command(["git", "merge", branch_name])


@git_app.command(name="analyze")
def git_analyze(
    path: str = typer.Argument(".", help="Ruta del repositorio Git a analizar."),
    prompt: str = typer.Option(
        "Resume los cambios recientes y sugiere próximos pasos.",
        "--prompt",
        "-p",
        help="Prompt para la IA.",
    ),
):
    """
    Analiza el log de Git de un repositorio usando IA.
    """
    typer.echo(f"Analizando repositorio Git en: {path}")
    try:
        # Obtener el log de commits
        result = subprocess.run(
            ["git", "log", "--pretty=format:%h - %an, %ar : %s", "-n20"],
            capture_output=True,
            text=True,
            check=True,
            cwd=path,
        )
        git_log_output = result.stdout

        if not git_log_output.strip():
            typer.echo("No hay commits en este repositorio para analizar.")
            return

        full_prompt = f"Eres un experto en desarrollo de software y análisis de proyectos. Analiza el siguiente log de commits de Git y proporciona un resumen conciso de los cambios recientes. Luego, sugiere posibles próximos pasos o áreas de enfoque para el desarrollo del proyecto. \n\nLog de Commits:\n{git_log_output}\n\nAnálisis y Sugerencias:"

        typer.echo("🤖 Enviando log a Gemini para análisis...")
        analysis_result = generar_idea(full_prompt)

        typer.secho("\n--- ANÁLISIS DE GIT POR IA ---", fg=typer.colors.CYAN)
        typer.echo(analysis_result)
        typer.secho("------------------------------", fg=typer.colors.CYAN)

    except subprocess.CalledProcessError as e:
        typer.secho(f"Error al obtener el log de Git: {e.stderr}", fg=typer.colors.RED)
    except FileNotFoundError:
        typer.secho(
            "Error: Git no encontrado o el directorio no es un repositorio Git.",
            fg=typer.colors.RED,
        )
    except Exception as e:
        typer.secho(
            f"Ha ocurrido un error inesperado durante el análisis: {e}",
            fg=typer.colors.RED,
        )
