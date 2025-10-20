import os

import yaml
from flask import (
    Blueprint,
    current_app,
    flash,
    jsonify,
    redirect,
    render_template,
    url_for,
)

playbooks_bp = Blueprint(
    "playbooks", __name__, template_folder="../templates", static_folder="../static"
)

PLAYBOOKS_DIR = "playbooks"


def get_playbooks():
    """Scans the playbooks directory and parses basic info from each playbook file."""
    playbooks = []
    if not os.path.exists(PLAYBOOKS_DIR):
        return []

    for filename in os.listdir(PLAYBOOKS_DIR):
        if filename.endswith((".yml", ".yaml")):
            file_path = os.path.join(PLAYBOOKS_DIR, filename)
            playbook_info = {
                "filename": filename,
                "name": "N/A",
                "description": "No se pudo leer el archivo.",
            }
            try:
                with open(file_path, "r") as f:
                    content = yaml.safe_load(f)
                    if isinstance(content, dict):
                        playbook_info["name"] = content.get("name", filename)
                        playbook_info["description"] = content.get(
                            "description", "Sin descripción."
                        )
            except Exception as e:
                current_app.logger.error(f"Error parsing playbook {filename}: {e}")

            playbooks.append(playbook_info)
    return playbooks


@playbooks_bp.route("/playbooks")
def list_playbooks():
    """Renders the main page for playbook management."""
    playbooks = get_playbooks()
    # Get connected agents for the 'Run' modal
    connected_agents = list(current_app.connected_agents.values())
    return render_template(
        "playbooks.html",
        playbooks=playbooks,
        agents=connected_agents,
        title="Gestión de Playbooks",
    )


# Placeholder for future implementation
@playbooks_bp.route("/playbooks/run/<string:filename>", methods=["POST"])
def run_playbook(filename):
    from flask import request

    agent_id = request.form.get("agent_id")
    playbook_path = os.path.join(PLAYBOOKS_DIR, filename)

    if not agent_id:
        flash("Debes seleccionar un agente de destino.", "danger")
        return redirect(url_for("playbooks.list_playbooks"))

    if not os.path.exists(playbook_path):
        flash(f"El playbook {filename} no fue encontrado.", "danger")
        return redirect(url_for("playbooks.list_playbooks"))

    current_app.playbook_executor.run_playbook_from_file(playbook_path, agent_id)

    flash(f'Ejecutando el playbook "{filename}" en el agente {agent_id}.', "info")
    return redirect(
        url_for("playbooks.list_playbooks")
    )  # Redirect to a dedicated execution log page in the future


@playbooks_bp.route("/playbooks/editor")
def playbook_editor():
    """Renders the visual playbook editor."""
    return render_template("playbook_editor.html", title="Editor Visual de Playbooks")


@playbooks_bp.route("/api/playbooks/run/<string:filename>", methods=["POST"])
def api_run_playbook(filename):
    """API endpoint to run a playbook asynchronously."""
    from flask import request

    data = request.get_json()
    agent_id = data.get("agent_id")
    playbook_path = os.path.join(PLAYBOOKS_DIR, filename)

    if not agent_id:
        return jsonify({"error": "agent_id is required"}), 400

    if not os.path.exists(playbook_path):
        return jsonify({"error": f"Playbook {filename} not found"}), 404

    # Check if agent is connected
    if agent_id not in current_app.connected_agents:
        return jsonify({"error": f"Agent {agent_id} is not connected"}), 400

    try:
        current_app.playbook_executor.run_playbook_from_file(playbook_path, agent_id)
        return jsonify({"message": f'Playbook "{filename}" initiated on agent {agent_id}.'})
    except Exception as e:
        current_app.logger.error(f"Error running playbook via API: {e}")
        return jsonify({"error": "An internal error occurred"}), 500
