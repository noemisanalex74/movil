import requests
from flask import Blueprint, flash, render_template
from models import Setting

github_bp = Blueprint("github", __name__)


@github_bp.route("/repos")
def list_repos():
    """Fetches and displays the user's GitHub repositories."""
    github_token_setting = Setting.query.filter_by(key="GITHUB_TOKEN").first()

    if not github_token_setting or not github_token_setting.value:
        flash(
            "Tu Token de GitHub no está configurado. Por favor, añádelo en la página de Ajustes.",
            "warning",
        )
        return render_template("github_repos.html", repos=None)

    token = github_token_setting.value
    headers = {
        "Authorization": f"token {token}",
        "Accept": "application/vnd.github.v3+json",
    }
    url = "https://api.github.com/user/repos?sort=pushed&per_page=50"

    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()  # Raise an exception for bad status codes
        repos = response.json()
        return render_template("github_repos.html", repos=repos)
    except requests.exceptions.RequestException as e:
        error_message = f"Error al contactar con la API de GitHub: {e}"
        if e.response is not None:
            if e.response.status_code == 401:
                error_message = "Error de autenticación. Tu Token de GitHub podría ser inválido o haber expirado."
            else:
                error_message = f"Error de la API de GitHub (código {e.response.status_code}): {e.response.text}"

        flash(error_message, "danger")
        return render_template("github_repos.html", repos=None)
