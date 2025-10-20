import base64
import os
import re
import uuid

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

mcp_bp = Blueprint("mcp", __name__)

# Define paths locally
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CUSTOM_TOOLS_DIR = os.path.join(BASE_DIR, "..", "instance", "custom_tools")
AGENT_REMOTE_MCPS_DIR = os.path.join(BASE_DIR, "..", "instance", "remote_mcps")


def _get_custom_tools_data():
    if not os.path.exists(CUSTOM_TOOLS_DIR):
        return []

    tools_data = []
    for filename in os.listdir(CUSTOM_TOOLS_DIR):
        if filename.endswith(".py"):
            base_name, ext = os.path.splitext(filename)
            version = ""
            display_name = base_name

            # Extraer la versión del nombre del archivo
            match = re.search(r"_v(\d+(_\d+)*)", base_name)
            if match:
                version = match.group(1).replace("_", ".")
                display_name = base_name.split("_v")[0]  # Nombre sin la versión

            tools_data.append(
                {"filename": filename, "base_name": display_name, "version": version}
            )
    return tools_data


def _read_mcp_file(filename):
    file_path = os.path.join(CUSTOM_TOOLS_DIR, filename)
    try:
        with open(file_path, "r") as f:
            return f.read()
    except FileNotFoundError:
        return None


def _write_mcp_file(filename, content):
    file_path = os.path.join(CUSTOM_TOOLS_DIR, filename)
    try:
        os.makedirs(CUSTOM_TOOLS_DIR, exist_ok=True)
        with open(file_path, "w") as f:
            f.write(content)
    except (IOError, OSError) as e:
        current_app.logger.error(f"Error al escribir el archivo MCP {file_path}: {e}")
        raise


def _delete_mcp_file(filename):
    file_path = os.path.join(CUSTOM_TOOLS_DIR, filename)
    try:
        if os.path.exists(file_path):
            os.remove(file_path)
        else:
            current_app.logger.warning(
                f"Intento de eliminar MCP que no existe: {file_path}"
            )
    except OSError as e:
        current_app.logger.error(f"Error al eliminar el archivo MCP {file_path}: {e}")
        raise


def _read_mcp_requirements_file(filename):
    req_file_path = os.path.join(CUSTOM_TOOLS_DIR, f"{filename}.requirements.txt")
    try:
        with open(req_file_path, "r") as f:
            return f.read()
    except FileNotFoundError:
        return ""  # Retornar cadena vacía si no existe
    except Exception as e:
        current_app.logger.error(
            f"Error al leer el archivo de requisitos {req_file_path}: {e}"
        )
        return ""


def _write_mcp_requirements_file(filename, content):
    req_file_path = os.path.join(CUSTOM_TOOLS_DIR, f"{filename}.requirements.txt")
    try:
        if content.strip():  # Solo escribir si hay contenido
            os.makedirs(CUSTOM_TOOLS_DIR, exist_ok=True)
            with open(req_file_path, "w") as f:
                f.write(content)
        elif os.path.exists(
            req_file_path
        ):  # Si no hay contenido y el archivo existe, eliminarlo
            os.remove(req_file_path)
    except (IOError, OSError) as e:
        current_app.logger.error(
            f"Error al escribir el archivo de requisitos {req_file_path}: {e}"
        )
        raise


@mcp_bp.route("/mcp")
def mcp_manager():
    page = request.args.get("page", 1, type=int)
    per_page = 10  # Número de MCPs por página
    search_query = request.args.get("search", "").strip().lower()

    all_tools = _get_custom_tools_data()

    if search_query:
        filtered_tools = [
            tool
            for tool in all_tools
            if search_query in tool["filename"].lower()
            or search_query in tool["base_name"].lower()
        ]
    else:
        filtered_tools = all_tools

    total_tools = len(filtered_tools)
    total_pages = (total_tools + per_page - 1) // per_page

    start = (page - 1) * per_page
    end = start + per_page
    tools_paginated = filtered_tools[start:end]

    agents = current_app.connected_agents.values()

    return render_template(
        "mcp_manager.html",
        tools=tools_paginated,
        page=page,
        per_page=per_page,
        total_pages=total_pages,
        total_tools=total_tools,
        search_query=search_query,
        agents=agents,
    )


@mcp_bp.route("/mcp_add", methods=["GET", "POST"])
def mcp_add():
    if request.method == "POST":
        filename = request.form["filename"]
        content = request.form["content"]
        requirements_content = request.form.get("requirements_content", "")
        version = request.form.get("version", "").strip()

        base_name, ext = os.path.splitext(filename)
        if version:
            version_suffix = "_v" + version.replace(".", "_")
            filename_with_version = f"{base_name}{version_suffix}{ext}"
        else:
            filename_with_version = filename

        if not filename_with_version.endswith(".py"):
            filename_with_version += ".py"

        try:
            _write_mcp_file(filename_with_version, content)
            _write_mcp_requirements_file(filename_with_version, requirements_content)
            flash(
                f"Herramienta personalizada {filename_with_version} guardada correctamente.",
                "success",
            )
            return redirect(url_for(".mcp_manager"))
        except (IOError, OSError) as e:
            current_app.logger.error(
                f"Error al añadir MCP {filename_with_version}: {e}"
            )
            flash(
                f"Error al guardar la herramienta personalizada {filename_with_version}. Por favor, inténtalo de nuevo.",
                "danger",
            )
    return render_template(
        "mcp_form.html",
        title="Añadir Nueva Herramienta Personalizada",
        tool={"filename": "", "content": "", "requirements_content": "", "version": ""},
    )


@mcp_bp.route("/mcp_edit/<filename>", methods=["GET", "POST"])
def mcp_edit(filename):
    if request.method == "POST":
        content = request.form["content"]
        requirements_content = request.form.get("requirements_content", "")
        version = request.form.get("version", "").strip()

        base_name, ext = os.path.splitext(filename)
        if "_v" in base_name:
            base_name = base_name.split("_v")[0]

        if version:
            version_suffix = "_v" + version.replace(".", "_")
            new_filename = f"{base_name}{version_suffix}{ext}"
        else:
            new_filename = f"{base_name}{ext}"

        if not new_filename.endswith(".py"):
            new_filename += ".py"

        try:
            if filename != new_filename:
                _delete_mcp_file(filename)
                old_req_file_path = os.path.join(
                    CUSTOM_TOOLS_DIR, f"{filename}.requirements.txt"
                )
                if os.path.exists(old_req_file_path):
                    os.remove(old_req_file_path)

            _write_mcp_file(new_filename, content)
            _write_mcp_requirements_file(new_filename, requirements_content)
            flash(
                f"Herramienta personalizada {new_filename} actualizada correctamente.",
                "success",
            )
            return redirect(url_for(".mcp_manager"))
        except (IOError, OSError) as e:
            current_app.logger.error(f"Error al editar MCP {new_filename}: {e}")
            flash(
                f"Error al actualizar la herramienta personalizada {new_filename}. Por favor, inténtalo de nuevo.",
                "danger",
            )

    content = _read_mcp_file(filename)
    requirements_content = _read_mcp_requirements_file(filename)

    version = ""
    base_name, ext = os.path.splitext(filename)
    match = re.search(r"_v(\d+(_\d+)*)", base_name)
    if match:
        version = match.group(1).replace("_", ".")

    if content is None:
        current_app.logger.warning(f"Intento de editar MCP no encontrado: {filename}")
        flash("Herramienta personalizada no encontrada.", "danger")
        return redirect(url_for("mcp.mcp_manager"))

    return render_template(
        "mcp_form.html",
        title=f"Editar {filename}",
        tool={
            "filename": filename,
            "content": content,
            "requirements_content": requirements_content,
            "version": version,
        },
    )


@mcp_bp.route("/mcp_delete/<filename>")
def mcp_delete(filename):
    try:
        _delete_mcp_file(filename)
        flash(
            f"Herramienta personalizada {filename} eliminada correctamente.", "success"
        )
    except OSError as e:
        current_app.logger.error(f"Error al eliminar MCP {filename}: {e}")
        flash(
            f"Error al eliminar la herramienta personalizada {filename}. Por favor, inténtalo de nuevo.",
            "danger",
        )
    return redirect(url_for("mcp.mcp_manager"))


@mcp_bp.route("/send_mcp_to_agent/<agent_id>/<mcp_name>")
def send_mcp_to_agent(agent_id, mcp_name):
    agent_data = current_app.connected_agents.get(agent_id)
    if not agent_data or agent_data["status"] != "online":
        flash(f"Agente {agent_id} no conectado o no encontrado.", "danger")
        return redirect(url_for("mcp.mcp_manager"))

    mcp_file_path = os.path.join(CUSTOM_TOOLS_DIR, mcp_name)
    if not os.path.exists(mcp_file_path):
        flash(f"MCP '{mcp_name}' no encontrado en el servidor del dashboard.", "danger")
        return redirect(url_for("mcp.mcp_manager"))

    try:
        with open(mcp_file_path, "rb") as f:
            file_content = f.read()
        file_content_base64 = base64.b64encode(file_content).decode("utf-8")

        remote_path = os.path.join(AGENT_REMOTE_MCPS_DIR, mcp_name)
        task_id = str(uuid.uuid4())

        current_app.socketio.emit(
            "upload_file",
            {
                "file_path": remote_path,
                "file_content_base64": file_content_base64,
                "task_id": task_id,
                "description": f"Transferencia de MCP: {mcp_name}",
            },
            room=agent_data["sid"],
            namespace="/agent",
        )

        flash(
            f"MCP '{mcp_name}' enviado al agente {agent_id} para su despliegue. ID de Tarea: {task_id}",
            "success",
        )
    except Exception as e:
        current_app.logger.error(
            f"Error al enviar MCP '{mcp_name}' al agente {agent_id}: {e}"
        )
        flash(f"Error al enviar MCP '{mcp_name}' al agente {agent_id}: {e}", "danger")

    return redirect(url_for("mcp.mcp_manager"))


@mcp_bp.route("/install_mcp_dependencies/<agent_id>", methods=["POST"])
def install_mcp_dependencies(agent_id):
    agent_data = current_app.connected_agents.get(agent_id)
    if not agent_data or agent_data["status"] != "online":
        flash(f"Agente {agent_id} no conectado o no encontrado.", "danger")
        return redirect(url_for("mcp.mcp_manager"))

    requirements_content = request.form.get("requirements_content")
    if not requirements_content:
        flash("No se proporcionó contenido para requirements.txt.", "danger")
        return redirect(url_for("mcp.mcp_manager"))

    try:
        task_id = str(uuid.uuid4())

        current_app.socketio.emit(
            "install_dependencies",
            {
                "requirements_content": requirements_content,
                "task_id": task_id,
                "description": "Instalación de dependencias de MCP",
            },
            room=agent_data["sid"],
            namespace="/agent",
        )

        flash(
            f"Solicitud de instalación de dependencias enviada al agente {agent_id}. ID de Tarea: {task_id}",
            "success",
        )
    except Exception as e:
        current_app.logger.error(
            f"Error al enviar solicitud de instalación de dependencias al agente {agent_id}: {e}"
        )
        flash(
            f"Error al enviar solicitud de instalación de dependencias al agente {agent_id}: {e}",
            "danger",
        )

    return redirect(url_for("mcp.mcp_manager"))


@mcp_bp.route("/execute_mcp_on_agent/<agent_id>/<mcp_name>")
def execute_mcp_on_agent(agent_id, mcp_name):
    agent_data = current_app.connected_agents.get(agent_id)
    if not agent_data or agent_data["status"] != "online":
        flash(f"Agente {agent_id} no conectado o no encontrado.", "danger")
        return redirect(url_for("mcp.mcp_manager"))

    try:
        task_id = str(uuid.uuid4())

        current_app.socketio.emit(
            "execute_mcp",
            {
                "mcp_name": mcp_name,
                "task_id": task_id,
                "description": f"Ejecución de MCP: {mcp_name}",
            },
            room=agent_data["sid"],
            namespace="/agent",
        )

        flash(
            f"Solicitud de ejecución de MCP '{mcp_name}' enviada al agente {agent_id}. ID de Tarea: {task_id}",
            "success",
        )
    except Exception as e:
        current_app.logger.error(
            f"Error al enviar solicitud de ejecución de MCP '{mcp_name}' al agente {agent_id}: {e}"
        )
        flash(
            f"Error al enviar solicitud de ejecución de MCP '{mcp_name}' al agente {agent_id}: {e}",
            "danger",
        )

    return redirect(url_for("mcp.mcp_manager"))


@mcp_bp.route("/get_mcp_requirements/<mcp_name>")
def get_mcp_requirements(mcp_name):
    requirements_content = _read_mcp_requirements_file(mcp_name)
    return jsonify(requirements_content=requirements_content)
