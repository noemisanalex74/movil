# agp-dashboard-web/blueprints/enterprise.py
import os

import requests
from flask import (
    Blueprint,
    current_app,
    flash,
    jsonify,
    redirect,
    render_template,
    request,
    url_for,
)
from models import Agent
from utils import _load_json

enterprise_bp = Blueprint("enterprise", __name__, url_prefix="/enterprise")

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
EMPRESAS_FILE = os.path.join(BASE_DIR, "instance", "empresas.json")

@enterprise_bp.route("/empresa/<empresa_id>")
def empresa_dashboard(empresa_id):
    empresas = _load_json(EMPRESAS_FILE, [])
    empresa = next((e for e in empresas if e.get('id') == empresa_id), None)
    if not empresa:
        flash("Empresa no encontrada.", "danger")
        return redirect(url_for('tasks.empresas_manager'))
    
    # Placeholder for associated agents and playbooks
    associated_agents = Agent.query.limit(2).all()
    available_playbooks = _load_json(os.path.join(BASE_DIR, "playbooks.json"), {}).get("playbooks", [])[:3]

    return render_template("enterprise/empresa_dashboard.html", 
                           empresa=empresa, 
                           agents=associated_agents, 
                           playbooks=available_playbooks)



@enterprise_bp.route("/list")
def list_agents():
    agents = Agent.query.all()
    for agent in agents:
        agent.is_online = any(
            a.get("id") == agent.agent_id for a in current_app.connected_agents.values()
        )
    return render_template("enterprise/agents.html", agents=agents)


@enterprise_bp.route("/network")
def agent_network():
    return render_template("enterprise/network.html")


@enterprise_bp.route("/network/data")
def agent_network_data():
    agents = Agent.query.all()
    nodes = []
    edges = []
    nodes.append(
        {
            "id": "dashboard",
            "label": "Dashboard",
            "shape": "icon",
            "icon": {
                "face": "'Bootstrap-Icons'",
                "code": "\uf2d2",
                "size": 60,
                "color": "#0d6efd",
            },
            "fixed": True,
        }
    )
    for agent in agents:
        is_online = any(
            a.get("id") == agent.agent_id for a in current_app.connected_agents.values()
        )
        color = "#198754" if is_online else "#dc3545"
        nodes.append(
            {
                "id": agent.agent_id,
                "label": agent.name,
                "shape": "icon",
                "icon": {
                    "face": "'Bootstrap-Icons'",
                    "code": "\uf5a2",
                    "size": 50,
                    "color": color,
                },
            }
        )
        edges.append({"from": "dashboard", "to": agent.agent_id})
    return jsonify({"nodes": nodes, "edges": edges})


@enterprise_bp.route("/agent/<agent_id>")
def agent_details(agent_id):
    agent = Agent.query.filter_by(agent_id=agent_id).first_or_404()
    agent.is_online = any(
        a.get("id") == agent.agent_id for a in current_app.connected_agents.values()
    )
    return render_template("enterprise/agent_details.html", agent=agent)


@enterprise_bp.route("/agent/<agent_id>/commands", methods=["GET", "POST"])
def manage_agent_commands(agent_id):
    agent = Agent.query.filter_by(agent_id=agent_id).first()

    if not agent:
        flash(f"Agente con ID {agent_id} no encontrado.", "danger")
        return redirect(url_for("enterprise.list_agents"))

    agent_url = f"http://{agent['ip']}:{agent.get('port', 5001)}"

    if request.method == "POST":
        action = request.form.get("action")
        command_name = request.form.get("name")

        api_endpoint = None
        payload = {}

        if action == "add":
            api_endpoint = f"{agent_url}/commands/add"
            payload = {
                "name": command_name,
                "command": request.form.get("command"),
                "description": request.form.get("description"),
            }
        elif action == "delete":
            api_endpoint = f"{agent_url}/commands/delete"
            payload = {"name": command_name}

        if api_endpoint:
            try:
                response = requests.post(api_endpoint, json=payload, timeout=10)
                response.raise_for_status()
                flash(
                    response.json().get("message", "Operación completada."), "success"
                )
            except requests.exceptions.HTTPError as e:
                error_details = e.response.json().get("error", e.response.text)
                flash(f"Error del agente: {error_details}", "danger")
            except requests.exceptions.RequestException as e:
                flash(f"Error de conexión con el agente: {e}", "danger")

        return redirect(url_for("enterprise.manage_agent_commands", agent_id=agent_id))

    # GET request logic
    commands = []
    try:
        response = requests.get(f"{agent_url}/commands", timeout=10)
        response.raise_for_status()
        commands = response.json()
    except requests.exceptions.RequestException as e:
        flash(f"No se pudieron obtener los comandos del agente: {e}", "danger")

    return render_template(
        "enterprise/manage_commands.html",
        agent=agent,
        agent_id=agent_id,
        commands=commands,
    )
