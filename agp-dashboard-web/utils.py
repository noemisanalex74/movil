import base64
import json
import logging
import os
from collections import Counter
from datetime import datetime

import requests
from cryptography.fernet import Fernet

# Import models and db within the function to avoid circular imports
# from models import AuditLog
# from extensions import db

# Configuración del logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
app_logger = logging.getLogger(__name__)

# Directorios de configuración
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
AGENT_REMOTE_MCPS_DIR = os.path.join(BASE_DIR, "instance", "remote_mcps")
CUSTOM_TOOLS_DIR = os.path.join(BASE_DIR, "instance", "custom_tools")
TAREAS_FILE = os.path.join(BASE_DIR, "instance", "tareas.json")


def _load_json(file_path, default_value=None):
    if not os.path.exists(file_path):
        return default_value if default_value is not None else {}
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            return json.load(f)
    except json.JSONDecodeError:
        return default_value if default_value is not None else {}


def _save_json(file_path, data):
    try:
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=4)
    except (IOError, OSError) as e:
        app_logger.error(f"Error al guardar el archivo JSON {file_path}: {e}")
        raise  # Re-lanzar la excepción para que la función que llama pueda manejarla


def _cargar_tareas():
    return _load_json(TAREAS_FILE, [])


def _guardar_tareas(tareas):
    _save_json(TAREAS_FILE, tareas)


# --- Funciones de Carga y Guardado de Datos (actualizadas) ---


def _cargar_config(CONFIG_FILE):
    return _load_json(CONFIG_FILE)


def _guardar_config(CONFIG_FILE, config):
    _save_json(CONFIG_FILE, config)


def _cargar_context_memory(CONTEXT_MEMORY_FILE):
    return _load_json(CONTEXT_MEMORY_FILE, {})


def _guardar_context_memory(CONTEXT_MEMORY_FILE, context_memory):
    _save_json(CONTEXT_MEMORY_FILE, context_memory)


def _cargar_proyectos():
    """Carga todos los proyectos desde la base de datos y los devuelve como una lista de diccionarios."""
    from models import Project
    projects_from_db = Project.query.order_by(Project.last_modified.desc()).all()
    projects_list = [
        {
            "id": p.id,
            "nombre": p.name,
            "descripcion": p.description,
            "ruta": p.path,
            "estado": p.status,
            "ultima_modificacion": p.last_modified.isoformat() if p.last_modified else None
        }
        for p in projects_from_db
    ]
    return projects_list

def _guardar_proyectos(proyectos):
    """Función obsoleta. La gestión de proyectos ahora se hace a través de los modelos de SQLAlchemy."""
    # Esta función se deja como placeholder. Las operaciones CRUD deben realizarse
    # directamente en la base de datos a través de los modelos y vistas correspondientes.
    app_logger.warning("La función _guardar_proyectos está obsoleta y no debería ser utilizada.")
    pass


def _get_virtual_envs_data(ENV_DIR):
    if not os.path.exists(ENV_DIR):
        return []
    # Asume que los entornos virtuales son subdirectorios en ENV_DIR
    return [d for d in os.listdir(ENV_DIR) if os.path.isdir(os.path.join(ENV_DIR, d))]


def _get_gemini_api_key(CONFIG_FILE):
    config = _cargar_config(CONFIG_FILE)
    api_key = config.get("gemini_api_key")
    if not api_key:
        raise ValueError("API Key de Gemini no configurada en config.json")
    return api_key


def _send_to_gemini_api(CONFIG_FILE, chat_history):
    api_key = _get_gemini_api_key(CONFIG_FILE)
    headers = {"Content-Type": "application/json", "x-goog-api-key": api_key}
    data = {"contents": chat_history}
    # Usar la URL de la API de Gemini para chat
    url = "https://generativelanguage.googleapis.com/v1beta/models/gemini-pro:generateContent"
    try:
        response = requests.post(url, headers=headers, json=data)
        response.raise_for_status()  # Lanza excepción para códigos de estado de error
        parts = response.json()["candidates"][0]["content"]["parts"][0]
        return parts["text"]
    except requests.exceptions.RequestException as e:
        app_logger.error(f"Error de red o API al comunicarse con Gemini: {e}")
        raise  # Re-lanzar la excepción para que la función que llama pueda manejarla


def _load_command_history(COMMAND_HISTORY_FILE):
    return _load_json(COMMAND_HISTORY_FILE, [])


def _save_command_history(COMMAND_HISTORY_FILE, history):
    _save_json(COMMAND_HISTORY_FILE, history)


def _load_agent_command_history(AGENT_COMMAND_HISTORY_FILE):
    return _load_json(AGENT_COMMAND_HISTORY_FILE, [])


def _save_agent_command_history(AGENT_COMMAND_HISTORY_FILE, history):
    _save_json(AGENT_COMMAND_HISTORY_FILE, history)


def _load_project_credentials(PROJECT_CREDENTIALS_FILE):
    return _load_json(PROJECT_CREDENTIALS_FILE, {})


def _save_project_credentials(PROJECT_CREDENTIALS_FILE, credentials):
    _save_json(PROJECT_CREDENTIALS_FILE, credentials)


def _load_allowed_commands(ALLOWED_COMMANDS_FILE):
    try:
        commands_list = _load_json(ALLOWED_COMMANDS_FILE, [])
        # Convert list of command dicts to a dict indexed by command name
        return {cmd["name"]: cmd for cmd in commands_list}
    except KeyError:
        app_logger.error(
            "Formato inválido en allowed_commands.json. "
            "Cada comando debe tener una clave 'name'."
        )
        return {}


def _save_allowed_commands(ALLOWED_COMMANDS_FILE, data):
    _save_json(ALLOWED_COMMANDS_FILE, data)


def _load_social_content(SOCIAL_CONTENT_FILE):
    return _load_json(SOCIAL_CONTENT_FILE, [])


def _save_social_content(SOCIAL_CONTENT_FILE, content):
    _save_json(SOCIAL_CONTENT_FILE, content)


def _cargar_empresas(EMPRESAS_FILE):
    return _load_json(EMPRESAS_FILE, [])


def _guardar_empresas(EMPRESAS_FILE, empresas):
    _save_json(EMPRESAS_FILE, empresas)


def _load_enterprise_agent_keys(ENTERPRISE_AGENT_KEYS_FILE):
    return _load_json(ENTERPRISE_AGENT_KEYS_FILE, {})


# --- User Management Functions ---
USERS_FILE = os.path.join(BASE_DIR, "instance", "users.json")


def _load_users():
    return _load_json(USERS_FILE, [])  # Users will be a list of dictionaries


def _save_users(users):
    _save_json(USERS_FILE, users)


# --- Agent Management Functions ---
AGENTS_FILE = os.path.join(BASE_DIR, "instance", "agents.json")


def _load_agents():
    return _load_json(AGENTS_FILE, [])  # Agents will be a list of dictionaries


def _save_agents(agents):
    _save_json(AGENTS_FILE, agents)


# --- Playbook Execution and Log Management Functions ---
PLAYBOOK_EXECUTIONS_FILE = os.path.join(
    BASE_DIR, "instance", "playbook_executions.json"
)
PLAYBOOK_LOGS_FILE = os.path.join(BASE_DIR, "instance", "playbook_logs.json")


def _load_playbook_executions():
    return _load_json(PLAYBOOK_EXECUTIONS_FILE, [])


def _save_playbook_executions(executions):
    _save_json(PLAYBOOK_EXECUTIONS_FILE, executions)


def _load_playbook_logs():
    return _load_json(PLAYBOOK_LOGS_FILE, [])


def _save_playbook_logs(logs):
    _save_json(PLAYBOOK_LOGS_FILE, logs)



def get_dashboard_stats(db, AgentTask, CustomTool):
    """Calcula las estadísticas para el dashboard principal."""
    try:
        # Cargar todas las fuentes de datos
        all_proyectos = _cargar_proyectos()
        all_tareas = _load_json(TAREAS_FILE, [])
        # TODO: Cargar MCPs desde su archivo JSON cuando se confirme la ruta
        all_mcps = _load_json(os.path.join(BASE_DIR, "instance", "mcps.json"), [])

        # --- Calcular Estadísticas de Tareas ---
        task_status_counts = Counter(t.get("estado", "desconocido") for t in all_tareas)

        ultima_tarea_completada = "N/A"
        completadas = [
            t for t in all_tareas
            if t.get("estado") == "completada" and t.get("fecha_modificacion")
        ]
        if completadas:
            try:
                completadas.sort(key=lambda x: x["fecha_modificacion"], reverse=True)
                ultima_tarea_completada = completadas[0].get("descripcion", "N/A")
                if len(ultima_tarea_completada) > 35:
                    ultima_tarea_completada = ultima_tarea_completada[:32] + "..."
            except (KeyError, TypeError) as e:
                app_logger.error(f"Error sorting completed tasks: {e}")
                ultima_tarea_completada = "Error de datos"


        # --- Calcular Estadísticas de Proyectos ---
        project_status_counts = Counter(
            p.get("estado", "desconocido") for p in all_proyectos
        )

        # --- Ensamblar el objeto de estadísticas ---
        stats = {
            "total_proyectos": len(all_proyectos),
            "tareas_pendientes": task_status_counts.get("pendiente", 0),
            "tareas_en_progreso": task_status_counts.get("en_progreso", 0),
            "tareas_completadas": task_status_counts.get("completada", 0),
            "mcps_registrados": len(all_mcps),
            "ultima_tarea_completada": ultima_tarea_completada,
            "project_status_counts": dict(project_status_counts),
            "task_status_counts": dict(task_status_counts)
        }

        return stats
    except Exception as e:
        app_logger.error(
            f"CRITICAL: Failed to calculate dashboard stats: {e}", exc_info=True
        )
        # Return a default/empty structure so the frontend doesn't crash
        return {
            "total_proyectos": 0,
            "tareas_pendientes": 0,
            "tareas_en_progreso": 0,
            "tareas_completadas": 0,
            "mcps_registrados": 0,
            "ultima_tarea_completada": "Error al cargar datos",
            "project_status_counts": {},
            "task_status_counts": {}
        }


def format_datetime(value, format='%d/%m/%Y %H:%M'):
    """Format a datetime string for display."""
    if not value:
        return ""
    try:
        # Attempt to parse ISO format
        dt = datetime.fromisoformat(value)
        return dt.strftime(format)
    except (ValueError, TypeError):
        return value # Return original if parsing fails


# --- Encryption Utilities ---

def get_fernet(app):
    key = app.config.get("SECRET_ENCRYPTION_KEY")
    if not key:
        raise ValueError(
            "SECRET_ENCRYPTION_KEY is not set in the application configuration."
        )
    # Ensure the key is 32 bytes and URL-safe base64 encoded.
    # This is a simple way to derive a key; a more robust method might use
    # a key derivation function like PBKDF2.
    encoded_key = key.encode()
    if len(encoded_key) < 32:
        encoded_key = encoded_key.ljust(32, b'=')
    else:
        encoded_key = encoded_key[:32]

    fernet_key = base64.urlsafe_b64encode(encoded_key)
    return Fernet(fernet_key)

def encrypt_value(app, value):
    fernet = get_fernet(app)
    return fernet.encrypt(value.encode())

def decrypt_value(app, encrypted_value):
    fernet = get_fernet(app)
    return fernet.decrypt(encrypted_value).decode()


def create_notification(user_id, message, url=None):
    from extensions import db, socketio
    from models import Notification

    notification = Notification(user_id=user_id, message=message, url=url)
    db.session.add(notification)
    db.session.commit()

    # Emit a socketio event to the specific user
    socketio.emit(
        "new_notification",
        {
            "id": notification.id,
            "message": notification.message,
            "timestamp": notification.timestamp.isoformat(),
            "url": notification.url,
        },
        room=f"user_{user_id}",
    )
