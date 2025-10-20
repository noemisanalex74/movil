import os
import uuid
from datetime import datetime

from flask import current_app, jsonify, request
from utils import _load_json, _save_json

from . import api_bp  # Importar el blueprint de la API

# Define la ruta al archivo de tareas relativamente al directorio de la app
# Asumimos que este blueprint está en /blueprints/api/
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
TAREAS_FILE = os.path.join(BASE_DIR, "instance", "tareas.json")

def _cargar_tareas():
    return _load_json(TAREAS_FILE, [])

def _guardar_tareas(tareas):
    _save_json(TAREAS_FILE, tareas)

@api_bp.route("/tasks")
def api_tasks():
    page = request.args.get("page", 1, type=int)
    per_page = 10
    search_query = request.args.get("search", "").strip().lower()
    sort_by = request.args.get("sort_by", "fecha_modificacion")
    sort_order = request.args.get("sort_order", "desc")

    all_tareas = _cargar_tareas()

    if search_query:
        all_tareas = [t for t in all_tareas if search_query in t.get("descripcion", "").lower()]

    # Ensure fecha_vencimiento is sortable even if null
    for t in all_tareas:
        if 'fecha_vencimiento' not in t:
            t['fecha_vencimiento'] = None

    if all_tareas:
        try:
            # Handle sorting for None values in fecha_vencimiento
            if sort_by == 'fecha_vencimiento':
                all_tareas.sort(
                    key=lambda x: (x[sort_by] is None, x[sort_by]), 
                    reverse=sort_order == "desc"
                )
            else:
                 all_tareas.sort(key=lambda x: x.get(sort_by, 0), reverse=sort_order == "desc")
        except (KeyError, TypeError):
            # Fallback if sort key is invalid
            pass

    total_tareas = len(all_tareas)
    total_pages = (total_tareas + per_page - 1) // per_page
    start = (page - 1) * per_page
    end = start + per_page
    tareas_paginadas = all_tareas[start:end]

    return jsonify({
        "tasks": tareas_paginadas,
        "page": page,
        "total_pages": total_pages,
        "total_tasks": total_tareas,
        "sort_by": sort_by,
        "sort_order": sort_order
    })

@api_bp.route("/tasks", methods=["POST"])
def create_task():
    data = request.get_json()
    if not data or "descripcion" not in data:
        return jsonify({"message": "Descripción de la tarea es requerida"}), 400

    descripcion = data["descripcion"]
    estado = data.get("estado", "pendiente")
    proyecto = data.get("proyecto", "")
    fecha_vencimiento = data.get("fecha_vencimiento")

    tareas = _cargar_tareas()

    nueva_tarea = {
        "id": str(uuid.uuid4()),
        "descripcion": descripcion,
        "estado": estado,
        "proyecto": proyecto,
        "fecha_modificacion": datetime.now().isoformat(),
        "fecha_vencimiento": fecha_vencimiento,
    }

    tareas.append(nueva_tarea)
    try:
        _guardar_tareas(tareas)
        # Opcional: emitir evento Socket.IO si es necesario
        # socketio.emit("new_task", {"descripcion": nueva_tarea["descripcion"]})
        return jsonify(nueva_tarea), 201
    except (IOError, OSError) as e:
        current_app.logger.error(f"Error al crear tarea vía API: {e}")
        return jsonify({"message": "Error interno del servidor al crear la tarea"}), 500

@api_bp.route("/tasks/<task_id>", methods=["PUT"])
def update_task(task_id):
    data = request.get_json()
    if not data:
        return jsonify({"message": "Datos de actualización son requeridos"}), 400

    tareas = _cargar_tareas()
    task_to_edit = next((t for t in tareas if t.get("id") == task_id), None)

    if task_to_edit is None:
        return jsonify({"message": "Tarea no encontrada"}), 404

    task_to_edit["descripcion"] = data.get("descripcion", task_to_edit["descripcion"])
    task_to_edit["estado"] = data.get("estado", task_to_edit["estado"])
    task_to_edit["proyecto"] = data.get("proyecto", task_to_edit["proyecto"])
    task_to_edit["fecha_vencimiento"] = data.get("fecha_vencimiento", task_to_edit["fecha_vencimiento"])
    task_to_edit["fecha_modificacion"] = datetime.now().isoformat()

    try:
        _guardar_tareas(tareas)
        # Opcional: emitir evento Socket.IO si es necesario
        # socketio.emit("update_task", {"descripcion": task_to_edit["descripcion"]})
        return jsonify(task_to_edit), 200
    except (IOError, OSError) as e:
        current_app.logger.error(f"Error al actualizar tarea {task_id} vía API: {e}")
        return jsonify({"message": "Error interno del servidor al actualizar la tarea"}), 500

@api_bp.route("/tasks/<task_id>", methods=["DELETE"])
def delete_task(task_id):
    tareas = _cargar_tareas()
    tareas_filtradas = [t for t in tareas if t.get("id") != task_id]

    if len(tareas) == len(tareas_filtradas):
        return jsonify({"message": "Tarea no encontrada"}), 404

    try:
        _guardar_tareas(tareas_filtradas)
        # Opcional: emitir evento Socket.IO si es necesario
        # socketio.emit("delete_task", {"descripcion": task_to_delete["descripcion"]})
        return jsonify({"message": "Tarea eliminada correctamente"}), 200
    except (IOError, OSError) as e:
        current_app.logger.error(f"Error al eliminar tarea {task_id} vía API: {e}")
        return jsonify({"message": "Error interno del servidor al eliminar la tarea"}), 500
