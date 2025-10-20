import os

import requests
import typer

github_app = typer.Typer(
    name="github", help="Comandos para interactuar con la API de GitHub."
)


def _get_github_token():
    """
    Obtiene el token de GitHub desde las variables de entorno.
    """
    token = os.environ.get("GITHUB_TOKEN")
    if not token:
        typer.secho(
            "Error: Token de GitHub no configurado. Usa el comando `agp setup` para configurarlo.",
            fg=typer.colors.RED,
        )
        raise typer.Abort()
    return token


def _get_authenticated_user_login():
    """
    Obtiene el login (nombre de usuario) del usuario autenticado en GitHub.
    """
    token = _get_github_token()
    headers = {
        "Authorization": f"token {token}",
        "Accept": "application/vnd.github.v3+json",
    }
    try:
        response = requests.get("https://api.github.com/user", headers=headers)
        response.raise_for_status()
        user_info = response.json()
        return user_info.get("login")
    except requests.exceptions.RequestException as e:
        typer.secho(f"Error al obtener el usuario de GitHub: {e}", fg=typer.colors.RED)
        raise typer.Abort()


# El comando 'auth' ha sido eliminado. La autenticación ahora se gestiona de forma centralizada
# con el comando `agp setup`, que guarda el token en el archivo .env.


@github_app.command(name="create-repo")
def create_repo(
    name: str = typer.Argument(..., help="Nombre del nuevo repositorio."),
    description: str = typer.Option(
        "", "--description", "-d", help="Descripción del repositorio."
    ),
    private: bool = typer.Option(
        False, "--private", "-p", help="Si el repositorio debe ser privado."
    ),
):
    """
    Crea un nuevo repositorio en GitHub.
    """
    token = _get_github_token()
    headers = {
        "Authorization": f"token {token}",
        "Accept": "application/vnd.github.v3+json",
    }
    data = {"name": name, "description": description, "private": private}

    typer.echo(f"Creando repositorio '{name}' en GitHub...")
    try:
        response = requests.post(
            "https://api.github.com/user/repos", headers=headers, json=data
        )
        response.raise_for_status()  # Lanza una excepción para errores HTTP
        repo_info = response.json()
        typer.secho(
            f"✅ Repositorio '{name}' creado con éxito: {repo_info['html_url']}",
            fg=typer.colors.GREEN,
        )
    except requests.exceptions.RequestException as e:
        typer.secho(f"Error al crear el repositorio: {e}", fg=typer.colors.RED)
        if response.status_code == 422:
            typer.secho(
                f"Detalles: {response.json()['errors'][0]['message']}",
                fg=typer.colors.RED,
            )


@github_app.command(name="list-repos")
def list_repos():
    """
    Lista los repositorios del usuario autenticado.
    """
    token = _get_github_token()
    headers = {
        "Authorization": f"token {token}",
        "Accept": "application/vnd.github.v3+json",
    }

    typer.echo("Listando repositorios de GitHub...")
    try:
        response = requests.get("https://api.github.com/user/repos", headers=headers)
        response.raise_for_status()
        repos = response.json()

        if not repos:
            typer.echo("No se encontraron repositorios.")
            return

        for repo in repos:
            typer.echo(
                f"- {repo['name']} ({repo['html_url']}) - {'Privado' if repo['private'] else 'Público'}"
            )

    except requests.exceptions.RequestException as e:
        typer.secho(f"Error al listar repositorios: {e}", fg=typer.colors.RED)


@github_app.command(name="create-issue")
def create_issue(
    repo_owner: str = typer.Argument(
        ...,
        help="Propietario del repositorio (tu nombre de usuario o el de la organización).",
    ),
    repo_name: str = typer.Argument(..., help="Nombre del repositorio."),
    title: str = typer.Argument(..., help="Título del issue."),
    body: str = typer.Option(None, "--body", "-b", help="Cuerpo del issue."),
):
    """
    Crea un nuevo issue en un repositorio de GitHub.
    """
    token = _get_github_token()
    headers = {
        "Authorization": f"token {token}",
        "Accept": "application/vnd.github.v3+json",
    }
    data = {"title": title, "body": body}

    typer.echo(f"Creando issue en {repo_owner}/{repo_name}...")
    try:
        response = requests.post(
            f"https://api.github.com/repos/{repo_owner}/{repo_name}/issues",
            headers=headers,
            json=data,
        )
        response.raise_for_status()
        issue_info = response.json()
        typer.secho(f"✅ Issue creado: {issue_info['html_url']}", fg=typer.colors.GREEN)
    except requests.exceptions.RequestException as e:
        typer.secho(f"Error al crear issue: {e}", fg=typer.colors.RED)


@github_app.command(name="list-issues")
def list_issues(
    repo_owner: str = typer.Argument(..., help="Propietario del repositorio."),
    repo_name: str = typer.Argument(..., help="Nombre del repositorio."),
    state: str = typer.Option(
        "open", "--state", "-s", help="Estado de los issues (open, closed, all)."
    ),
):
    """
    Lista los issues de un repositorio de GitHub.
    """
    token = _get_github_token()
    headers = {
        "Authorization": f"token {token}",
        "Accept": "application/vnd.github.v3+json",
    }

    typer.echo(f"Listando issues de {repo_owner}/{repo_name} (estado: {state})...")
    try:
        response = requests.get(
            f"https://api.github.com/repos/{repo_owner}/{repo_name}/issues?state={state}",
            headers=headers,
        )
        response.raise_for_status()
        issues = response.json()

        if not issues:
            typer.echo("No se encontraron issues.")
            return

        for issue in issues:
            typer.echo(
                f"- #{issue['number']}: {issue['title']} (Estado: {issue['state']}) - {issue['html_url']}"
            )

    except requests.exceptions.RequestException as e:
        typer.secho(f"Error al listar issues: {e}", fg=typer.colors.RED)


@github_app.command(name="close-issue")
def close_issue(
    repo_owner: str = typer.Argument(..., help="Propietario del repositorio."),
    repo_name: str = typer.Argument(..., help="Nombre del repositorio."),
    issue_number: int = typer.Argument(..., help="Número del issue a cerrar."),
):
    """
    Cierra un issue en un repositorio de GitHub.
    """
    token = _get_github_token()
    headers = {
        "Authorization": f"token {token}",
        "Accept": "application/vnd.github.v3+json",
    }
    data = {"state": "closed"}

    typer.echo(f"Cerrando issue #{issue_number} en {repo_owner}/{repo_name}...")
    try:
        response = requests.patch(
            f"https://api.github.com/repos/{repo_owner}/{repo_name}/issues/{issue_number}",
            headers=headers,
            json=data,
        )
        response.raise_for_status()
        issue_info = response.json()
        typer.secho(
            f"✅ Issue #{issue_number} cerrado: {issue_info['html_url']}",
            fg=typer.colors.GREEN,
        )
    except requests.exceptions.RequestException as e:
        typer.secho(f"Error al cerrar issue: {e}", fg=typer.colors.RED)


@github_app.command(name="list-pulls")
def list_pulls(
    repo_owner: str = typer.Argument(..., help="Propietario del repositorio."),
    repo_name: str = typer.Argument(..., help="Nombre del repositorio."),
    state: str = typer.Option(
        "open", "--state", "-s", help="Estado de los pull requests (open, closed, all)."
    ),
):
    """
    Lista los pull requests de un repositorio de GitHub.
    """
    token = _get_github_token()
    headers = {
        "Authorization": f"token {token}",
        "Accept": "application/vnd.github.v3+json",
    }

    typer.echo(
        f"Listando pull requests de {repo_owner}/{repo_name} (estado: {state})..."
    )
    try:
        response = requests.get(
            f"https://api.github.com/repos/{repo_owner}/{repo_name}/pulls?state={state}",
            headers=headers,
        )
        response.raise_for_status()
        pulls = response.json()

        if not pulls:
            typer.echo("No se encontraron pull requests.")
            return

        for pull in pulls:
            typer.echo(
                f"- #{pull['number']}: {pull['title']} (Estado: {pull['state']}) - {pull['html_url']}"
            )

    except requests.exceptions.RequestException as e:
        typer.secho(f"Error al listar pull requests: {e}", fg=typer.colors.RED)
