from flask import Blueprint, jsonify, request, url_for
from utils import _load_json

# Creamos el Blueprint para la API, con un prefijo de URL
api_bp = Blueprint('api', __name__, url_prefix='/api')

# Import API routes to register them
from . import empresas, projects, tasks  # noqa: F401

@api_bp.route("/search")
def unified_search():
    query = request.args.get("q", "").strip().lower()
    if not query:
        return jsonify([])

    results = []

    # 1. Search Tasks
    try:
        all_tareas = _load_json("instance/tareas.json", [])
        for t in all_tareas:
            if query in t.get("descripcion", "").lower():
                results.append({
                    "type": "Tarea",
                    "name": t.get("descripcion"),
                    "url": url_for('tasks.tasks_manager',
                                   search=t.get("descripcion")),
                    "icon": "bi-list-check"
                })
    except FileNotFoundError:
        pass # Ignore if file doesn't exist

    # 2. Search Projects
    try:
        all_proyectos = _load_json("instance/proyectos.json", [])
        for p in all_proyectos:
            if (query in p.get("nombre", "").lower() or
                query in p.get("descripcion", "").lower()):
                results.append({
                    "type": "Proyecto",
                    "name": p.get("nombre"),
                    "url": url_for('tasks.project_stats'),
                    "icon": "bi-folder-fill"
                })
    except FileNotFoundError:
        pass # Ignore if file doesn't exist

    # 3. Search Navigation Links
    nav_links = {
        "Kanban": {"url": url_for('tasks.kanban_tasks'),
                   "icon": "bi-kanban-fill"},
        "Ajustes": {"url": url_for('settings.settings_manager'),
                    "icon": "bi-gear-wide-connected"},
        "Ejecución Local": {"url": url_for('local_execution.execution_page'),
                            "icon": "bi-terminal-fill"},
        "Playbooks": {"url": url_for('playbooks.list_playbooks'),
                      "icon": "bi-file-earmark-play-fill"}
    }
    for name, data in nav_links.items():
        if query in name.lower():
            results.append({
                "type": "Navegación",
                "name": name,
                "url": data["url"],
                "icon": data["icon"]
            })

    # Limit results to e.g. 10
    return jsonify(results[:10])
