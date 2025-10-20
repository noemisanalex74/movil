import uuid
from datetime import datetime

from flask import current_app, jsonify, request
from utils import _cargar_proyectos, _guardar_proyectos

from . import api_bp


@api_bp.route("/projects", methods=["GET"])
def get_projects():
    page = request.args.get("page", 1, type=int)
    per_page = 10
    search_query = request.args.get("search", "").strip().lower()
    sort_by = request.args.get("sort_by", "ultima_modificacion")
    sort_order = request.args.get("sort_order", "desc")

    all_proyectos = _cargar_proyectos()

    if search_query:
        all_proyectos = [
            p for p in all_proyectos
            if search_query in p.get("nombre", "").lower() or
               search_query in p.get("descripcion", "").lower()
        ]

    if all_proyectos:
        try:
            all_proyectos.sort(key=lambda x: x.get(sort_by, ""), reverse=sort_order == "desc")
        except (KeyError, TypeError):
            pass # Fallback if sort key is invalid

    total_proyectos = len(all_proyectos)
    total_pages = (total_proyectos + per_page - 1) // per_page
    start = (page - 1) * per_page
    end = start + per_page
    proyectos_paginados = all_proyectos[start:end]

    return jsonify({
        "projects": proyectos_paginados,
        "page": page,
        "total_pages": total_pages,
        "total_projects": total_proyectos,
        "sort_by": sort_by,
        "sort_order": sort_order
    })

@api_bp.route("/projects", methods=["POST"])
def create_project():
    data = request.get_json()
    if not data or "nombre" not in data:
        return jsonify({"message": "El nombre del proyecto es requerido"}), 400

    nombre = data["nombre"]
    descripcion = data.get("descripcion", "")
    ruta = data.get("ruta", "")
    estado = data.get("estado", "activo")

    proyectos = _cargar_proyectos()

    nuevo_proyecto = {
        "id": str(uuid.uuid4()),
        "nombre": nombre,
        "descripcion": descripcion,
        "ruta": ruta,
        "estado": estado,
        "ultima_modificacion": datetime.now().isoformat(),
    }

    proyectos.append(nuevo_proyecto)
    try:
        _guardar_proyectos(proyectos)
        return jsonify(nuevo_proyecto), 201
    except (IOError, OSError) as e:
        current_app.logger.error(f"Error al crear proyecto vía API: {e}")
        return jsonify({"message": "Error interno del servidor al crear el proyecto"}), 500

@api_bp.route("/projects/<project_id>", methods=["PUT"])
def update_project(project_id):
    data = request.get_json()
    if not data:
        return jsonify({"message": "Datos de actualización son requeridos"}), 400

    proyectos = _cargar_proyectos()
    project_to_edit = next((p for p in proyectos if p.get("id") == project_id), None)

    if project_to_edit is None:
        return jsonify({"message": "Proyecto no encontrado"}), 404

    project_to_edit["nombre"] = data.get("nombre", project_to_edit["nombre"])
    project_to_edit["descripcion"] = data.get("descripcion", project_to_edit["descripcion"])
    project_to_edit["ruta"] = data.get("ruta", project_to_edit["ruta"])
    project_to_edit["estado"] = data.get("estado", project_to_edit["estado"])
    project_to_edit["ultima_modificacion"] = datetime.now().isoformat()

    try:
        _guardar_proyectos(proyectos)
        return jsonify(project_to_edit), 200
    except (IOError, OSError) as e:
        current_app.logger.error(f"Error al actualizar proyecto {project_id} vía API: {e}")
        return jsonify({"message": "Error interno del servidor al actualizar el proyecto"}), 500

@api_bp.route("/projects/<project_id>", methods=["DELETE"])
def delete_project(project_id):
    proyectos = _cargar_proyectos()
    proyectos_filtrados = [p for p in proyectos if p.get("id") != project_id]

    if len(proyectos) == len(proyectos_filtrados):
        return jsonify({"message": "Proyecto no encontrado"}), 404

    try:
        _guardar_proyectos(proyectos_filtrados)
        return jsonify({"message": "Proyecto eliminado correctamente"}), 200
    except (IOError, OSError) as e:
        current_app.logger.error(f"Error al eliminar proyecto {project_id} vía API: {e}")
        return jsonify({"message": "Error interno del servidor al eliminar el proyecto"}), 500
