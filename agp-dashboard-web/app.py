from flask import Flask, render_template, request, redirect, url_for, flash, get_flashed_messages, make_response, session, jsonify, g
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from flask_socketio import SocketIO, emit
import os
import json
import sys
import io
import subprocess
import csv
import pty
import select
import requests
import uuid
from datetime import datetime
from collections import Counter
import time
import logging
from flask_sqlalchemy import SQLAlchemy

# --- Configuración de la Aplicación ---
app = Flask(__name__)
socketio = SocketIO(app)

# Configuración del logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
app.logger.setLevel(logging.INFO)

@app.before_request
def before_request():
    g.cache_buster = int(time.time())


# Configuración de la SECRET_KEY (Más Segura)
SECRET_KEY = os.environ.get('SECRET_KEY')
if not SECRET_KEY:
    app.logger.warning("ADVERTENCIA: La SECRET_KEY no está configurada. Usando una clave temporal.")
    SECRET_KEY = os.urandom(24).hex()
app.config['SECRET_KEY'] = SECRET_KEY

# Configuración de la base de datos
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///site.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# Diccionario para almacenar procesos de terminal
terminals = {}

# --- Configuración de Flask-Login ---
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login' # La vista a la que se redirige si no está logueado
login_manager.login_message = "Por favor, inicia sesión para acceder a esta página."
login_manager.login_message_category = "info"

# --- Rutas Dinámicas ---
HOME_DIR = os.path.expanduser("~")
AGP_CLI_DIR = os.path.join(HOME_DIR, "agp-gemini-cli")
GEMINI_DIR = os.path.join(HOME_DIR, ".gemini")
DASHBOARD_DIR = os.path.join(HOME_DIR, "agp-dashboard-web")

# Definir rutas a los archivos de datos
CONFIG_FILE = os.path.join(AGP_CLI_DIR, "config.json")
TAREAS_FILE = os.path.join(AGP_CLI_DIR, "tareas.json")
CONTEXT_MEMORY_FILE = os.path.join(AGP_CLI_DIR, "context_memory.json")
CUSTOM_TOOLS_DIR = os.path.join(AGP_CLI_DIR, "custom_tools")
PROJECT_CREDENTIALS_FILE = os.path.join(AGP_CLI_DIR, "project_credentials.json")
PROYECTOS_FILE = os.path.join(GEMINI_DIR, "aprendizaje", "proyectos.json")
COMMAND_HISTORY_FILE = os.path.join(DASHBOARD_DIR, "command_history.json")
# USERS_FILE = os.path.join(DASHBOARD_DIR, "users.json") # Ya no se usa con la base de datos
ENV_DIR = os.path.join(HOME_DIR, ".virtualenvs")

# --- Modelo de Usuario para Flask-Login con SQLAlchemy ---
class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(20), unique=True, nullable=False)
    password_hash = db.Column(db.String(128), nullable=False)

    def __repr__(self):
        return f"User('{self.username}')"

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# --- Funciones Genéricas para JSON (mantener para otros archivos JSON) ---
def _load_json(file_path, default_value=None):
    if not os.path.exists(file_path):
        return default_value if default_value is not None else {}
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except json.JSONDecodeError:
        return default_value if default_value is not None else {}

def _save_json(file_path, data):
    try:
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=4)
    except (IOError, OSError) as e:
        app.logger.error(f"Error al guardar el archivo JSON {file_path}: {e}")
        raise # Re-lanzar la excepción para que la función que llama pueda manejarla

# --- Funciones de Carga y Guardado de Datos (actualizadas) ---
# _load_users() y _save_users() ya no son necesarias con la base de datos

def _migrate_users_from_json():
    users_file_path = os.path.join(DASHBOARD_DIR, "users.json")
    if os.path.exists(users_file_path):
        app.logger.info("Iniciando migración de usuarios desde users.json...")
        try:
            with open(users_file_path, 'r', encoding='utf-8') as f:
                json_users = json.load(f)

            for username, user_data in json_users.items():
                # Verificar si el usuario ya existe en la base de datos
                existing_user = User.query.filter_by(username=username).first()
                if not existing_user:
                    new_user = User(username=username, password_hash=user_data['password_hash'])
                    db.session.add(new_user)
                    app.logger.info(f"Usuario '{username}' migrado.")
                else:
                    app.logger.info(f"Usuario '{username}' ya existe en la base de datos, omitiendo.")
            db.session.commit()
            app.logger.info("Migración de usuarios completada.")
            # Eliminar el archivo users.json después de la migración exitosa
            os.remove(users_file_path)
            app.logger.info(f"Archivo {users_file_path} eliminado.")
        except json.JSONDecodeError:
            app.logger.error("Error al decodificar users.json. Archivo corrupto o vacío.")
        except Exception as e:
            db.session.rollback()
            app.logger.error(f"Error durante la migración de usuarios: {e}")
    else:
        app.logger.info("users.json no encontrado. No se requiere migración de usuarios.")

def _cargar_config():
    return _load_json(CONFIG_FILE)

def _guardar_config(config):
    _save_json(CONFIG_FILE, config)

def _cargar_tareas():
    return _load_json(TAREAS_FILE, [])

def _guardar_tareas(tareas):
    _save_json(TAREAS_FILE, tareas)

def _cargar_context_memory():
    return _load_json(CONTEXT_MEMORY_FILE, {})

def _guardar_context_memory(context_memory):
    _save_json(CONTEXT_MEMORY_FILE, context_memory)

def _get_custom_tools_data():
    if not os.path.exists(CUSTOM_TOOLS_DIR):
        return []
    return [f for f in os.listdir(CUSTOM_TOOLS_DIR) if f.endswith('.py')]

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
        app.logger.error(f"Error al escribir el archivo MCP {file_path}: {e}")
        raise

def _delete_mcp_file(filename):
    file_path = os.path.join(CUSTOM_TOOLS_DIR, filename)
    try:
        if os.path.exists(file_path):
            os.remove(file_path)
        else:
            app.logger.warning(f"Intento de eliminar MCP que no existe: {file_path}")
    except OSError as e:
        app.logger.error(f"Error al eliminar el archivo MCP {file_path}: {e}")
        raise

def _load_command_history():
    return _load_json(COMMAND_HISTORY_FILE, [])

def _save_command_history(history):
    _save_json(COMMAND_HISTORY_FILE, history)

def _load_project_credentials():
    return _load_json(PROJECT_CREDENTIALS_FILE, {})

def _save_project_credentials(credentials):
    _save_json(PROJECT_CREDENTIALS_FILE, credentials)

def _get_gemini_api_key():
    config = _cargar_config()
    api_key = config.get("gemini_api_key")
    if not api_key:
        raise ValueError("API Key de Gemini no configurada en config.json")
    return api_key

def _send_to_gemini_api(chat_history):
    api_key = _get_gemini_api_key()
    headers = {
        "Content-Type": "application/json",
        "x-goog-api-key": api_key
    }
    data = {
        "contents": chat_history
    }
    # Usar la URL de la API de Gemini para chat
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-pro:generateContent"
    try:
        response = requests.post(url, headers=headers, json=data)
        response.raise_for_status() # Lanza una excepción para códigos de estado de error
        return response.json()['candidates'][0]['content']['parts'][0]['text']
    except requests.exceptions.RequestException as e:
        app.logger.error(f"Error de red o API al comunicarse con Gemini: {e}")
        raise # Re-lanzar la excepción para que la función que llama pueda manejarla

def _cargar_proyectos():
    return _load_json(PROYECTOS_FILE, [])

def _get_virtual_envs_data():
    if not os.path.exists(ENV_DIR):
        return []
    # Asume que los entornos virtuales son subdirectorios en ENV_DIR
    return [d for d in os.listdir(ENV_DIR) if os.path.isdir(os.path.join(ENV_DIR, d))]

# --- Rutas de Autenticación ---
@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user_data = User.query.filter_by(username=username).first()

        if user_data and check_password_hash(user_data.password_hash, password):
            user = User.query.get(user_data.id)
            login_user(user)
            flash('Has iniciado sesión correctamente.', 'success')
            return redirect(url_for('dashboard'))
        else:
            flash('Usuario o contraseña incorrectos.', 'danger')

    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))

    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        confirm_password = request.form['confirm_password']

        if not username or not password or not confirm_password:
            flash('Todos los campos son obligatorios.', 'danger')
            return render_template('register.html')

        existing_user = User.query.filter_by(username=username).first()
        if existing_user:
            flash('El nombre de usuario ya existe.', 'danger')
            return render_template('register.html')

        if password != confirm_password:
            flash('Las contraseñas no coinciden.', 'danger')
            return render_template('register.html')

        hashed_password = generate_password_hash(password)
        new_user = User(username=username, password_hash=hashed_password)
        db.session.add(new_user)
        db.session.commit()
        flash('Registro exitoso. Por favor, inicia sesión.', 'success')
        return redirect(url_for('login'))

    return render_template('register.html')

@app.route('/logout')
def logout():
    logout_user()
    flash('Has cerrado sesión correctamente.', 'info')
    return redirect(url_for('login'))

# --- Rutas Protegidas ---
@app.route('/')
@login_required
def dashboard():
    all_proyectos = _cargar_proyectos()
    all_tareas = _cargar_tareas()
    all_mcps = _get_custom_tools_data()

    total_proyectos = len(all_proyectos)
    tareas_pendientes = len([t for t in all_tareas if t.get('estado') == 'pendiente'])
    mcps_registrados = len(all_mcps)

    # Última tarea completada
    completed_tasks = [t for t in all_tareas if t.get('estado') == 'completada' and t.get('fecha_modificacion')]
    ultima_tarea_completada = "N/A"
    if completed_tasks:
        # Ordenar por fecha de modificación descendente
        completed_tasks.sort(key=lambda x: x['fecha_modificacion'], reverse=True)
        ultima_tarea_completada = completed_tasks[0].get('descripcion', 'Tarea completada')

    stats = {
        'total_proyectos': total_proyectos,
        'tareas_pendientes': tareas_pendientes,
        'mcps_registrados': mcps_registrados,
        'ultima_tarea_completada': ultima_tarea_completada
    }

    # Actividad reciente (ejemplo, esto podría venir de un log o sistema de eventos real)
    recent_activity = [
        {'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'), 'description': 'Dashboard cargado.'},
        {'timestamp': '2025-08-08 10:30:00', 'description': 'Tarea "Implementar autenticación" completada.'},
        {'timestamp': '2025-08-07 15:00:00', 'description': 'Nuevo proyecto "Sistema de Gestión de Clientes" añadido.'},
    ]

    # Calcular estadísticas de proyectos por estado
    project_status_counts = Counter(p.get('estado', 'desconocido') for p in all_proyectos)

    # Calcular estadísticas de tareas por estado (ya que no hay prioridad)
    task_status_counts = Counter(t.get('estado', 'desconocido') for t in all_tareas)

    return render_template('dashboard.html',
                           stats=stats,
                           recent_activity=recent_activity,
                           project_status_counts=project_status_counts,
                           task_status_counts=task_status_counts)

@app.route('/mcp_manager')

def mcp_manager():
    page = request.args.get('page', 1, type=int)
    per_page = 10  # Número de MCPs por página
    search_query = request.args.get('search', '').strip().lower()

    all_tools = _get_custom_tools_data()

    if search_query:
        filtered_tools = [tool for tool in all_tools if search_query in tool.lower()]
    else:
        filtered_tools = all_tools

    total_tools = len(filtered_tools)
    total_pages = (total_tools + per_page - 1) // per_page
    
    start = (page - 1) * per_page
    end = start + per_page
    tools_paginated = filtered_tools[start:end]

    return render_template('mcp_manager.html', 
                           tools=tools_paginated, 
                           page=page, 
                           per_page=per_page, 
                           total_pages=total_pages, 
                           total_tools=total_tools, 
                           search_query=search_query)

@app.route('/mcp_add', methods=['GET', 'POST'])

def mcp_add():
    if request.method == 'POST':
        filename = request.form['filename']
        content = request.form['content']
        if not filename.endswith('.py'):
            filename += '.py'
        try:
            _write_mcp_file(filename, content)
            flash(f'Herramienta personalizada {filename} guardada correctamente.', 'success')
            return redirect(url_for('mcp_manager'))
        except (IOError, OSError) as e:
            app.logger.error(f"Error al añadir MCP {filename}: {e}")
            flash(f'Error al guardar la herramienta personalizada {filename}. Por favor, inténtalo de nuevo.', 'danger')
    return render_template('mcp_form.html', title='Añadir Nueva Herramienta Personalizada', tool={'filename': '', 'content': ''})

@app.route('/mcp_edit/<filename>', methods=['GET', 'POST'])

def mcp_edit(filename):
    if request.method == 'POST':
        content = request.form['content']
        try:
            _write_mcp_file(filename, content)
            flash(f'Herramienta personalizada {filename} actualizada correctamente.', 'success')
            return redirect(url_for('mcp_manager'))
        except (IOError, OSError) as e:
            app.logger.error(f"Error al editar MCP {filename}: {e}")
            flash(f'Error al actualizar la herramienta personalizada {filename}. Por favor, inténtalo de nuevo.', 'danger')
    
    content = _read_mcp_file(filename)
    if content is None:
        app.logger.warning(f"Intento de editar MCP no encontrado: {filename}")
        flash('Herramienta personalizada no encontrada.', 'danger')
        return redirect(url_for('mcp_manager'))
    
    return render_template('mcp_form.html', title=f'Editar {filename}', tool={'filename': filename, 'content': content})

@app.route('/mcp_delete/<filename>')

def mcp_delete(filename):
    try:
        _delete_mcp_file(filename)
        flash(f'Herramienta personalizada {filename} eliminada correctamente.', 'success')
    except OSError as e:
        app.logger.error(f"Error al eliminar MCP {filename}: {e}")
        flash(f'Error al eliminar la herramienta personalizada {filename}. Por favor, inténtalo de nuevo.', 'danger')
    return redirect(url_for('mcp_manager'))

@app.route('/tasks_manager')
def tasks_manager():
    search_query = request.args.get('search', '').strip().lower()

    all_tareas = _cargar_tareas()
    
    return render_template('tasks_manager.html', 
                           tareas=all_tareas, 
                           search_query=search_query)

@app.route('/task_add', methods=['GET', 'POST'])
def task_add():
    if request.method == 'POST':
        descripcion = request.form['descripcion']
        estado = request.form['estado']
        tareas = _cargar_tareas()
        
        # Crear nueva tarea con UUID y fecha de modificación
        nueva_tarea = {
            'id': str(uuid.uuid4()), 
            'descripcion': descripcion, 
            'estado': estado,
            'fecha_modificacion': datetime.now().isoformat()
        }
        
        tareas.append(nueva_tarea)
        try:
            _guardar_tareas(tareas)
            flash('Tarea añadida correctamente.', 'success')
            return redirect(url_for('tasks_manager'))
        except (IOError, OSError) as e:
            app.logger.error(f"Error al añadir tarea: {e}")
            flash('Error al añadir la tarea. Por favor, inténtalo de nuevo.', 'danger')
    return render_template('task_form.html', title='Añadir Nueva Tarea', task={'descripcion': '', 'estado': 'pendiente'})

@app.route('/task_edit/<task_id>', methods=['GET', 'POST'])
def task_edit(task_id):
    tareas = _cargar_tareas()
    task_to_edit = next((t for t in tareas if t.get('id') == task_id), None)

    if task_to_edit is None:
        flash('Tarea no encontrada.', 'error')
        return redirect(url_for('tasks_manager'))

    if request.method == 'POST':
        task_to_edit['descripcion'] = request.form['descripcion']
        task_to_edit['estado'] = request.form['estado']
        task_to_edit['fecha_modificacion'] = datetime.now().isoformat()
        try:
            _guardar_tareas(tareas)
            flash('Tarea actualizada correctamente.', 'success')
            return redirect(url_for('tasks_manager'))
        except (IOError, OSError) as e:
            app.logger.error(f"Error al actualizar tarea {task_id}: {e}")
            flash('Error al actualizar la tarea. Por favor, inténtalo de nuevo.', 'danger')
    
    return render_template('task_form.html', title=f'Editar Tarea', task=task_to_edit, task_id=task_id)

@app.route('/task_delete/<task_id>')
def task_delete(task_id):
    tareas = _cargar_tareas()
    # Filtrar la lista para eliminar la tarea con el ID especificado
    tareas_filtradas = [t for t in tareas if t.get('id') != task_id]

    if len(tareas) == len(tareas_filtradas):
        flash('Tarea no encontrada.', 'error')
    else:
        try:
            _guardar_tareas(tareas_filtradas)
            flash('Tarea eliminada correctamente.', 'success')
        except (IOError, OSError) as e:
            app.logger.error(f"Error al eliminar tarea {task_id}: {e}")
            flash('Error al eliminar la tarea. Por favor, inténtalo de nuevo.', 'danger')
        
    return redirect(url_for('tasks_manager'))

@app.route('/config_manager', methods=['GET', 'POST'])

def config_manager():
    config = _cargar_config()
    if request.method == 'POST':
        config['gemini_api_key'] = request.form['gemini_api_key']
        config['github_token'] = request.form['github_token']
        try:
            _guardar_config(config)
            flash('Configuración guardada correctamente.', 'success')
            return redirect(url_for('config_manager'))
        except (IOError, OSError) as e:
            app.logger.error(f"Error al guardar la configuración: {e}")
            flash('Error al guardar la configuración. Por favor, inténtalo de nuevo.', 'danger')
    return render_template('config_manager.html', config=config)

@app.route('/user_prefs_manager', methods=['GET', 'POST'])

def user_prefs_manager():
    context_memory = _cargar_context_memory()
    if request.method == 'POST':
        # Actualizar solo las preferencias, no todo el context_memory
        preferencias = context_memory.get("preferencias", {})
        for key, value in request.form.items():
            preferencias[key] = value
        context_memory["preferencias"] = preferencias
        try:
            _guardar_context_memory(context_memory)
            flash('Preferencias de usuario guardadas correctamente.', 'success')
            return redirect(url_for('user_prefs_manager'))
        except (IOError, OSError) as e:
            app.logger.error(f"Error al guardar las preferencias de usuario: {e}")
            flash('Error al guardar las preferencias de usuario. Por favor, inténtalo de nuevo.', 'danger')
    
    user_prefs_info = context_memory.get("preferencias", {})
    return render_template('user_prefs_manager.html', user_prefs_info=user_prefs_info)

@app.route('/logs')

def logs_viewer():
    log_content = ""
    log_file_path = os.path.join(app.root_path, 'flask.log')
    try:
        with open(log_file_path, 'r') as f:
            log_content = f.read()
    except FileNotFoundError:
        log_content = "No se encontró el archivo de log (flask.log)."
    return render_template('logs_viewer.html', log_content=log_content)

@app.route('/run_command', methods=['GET', 'POST'])

def run_command():
    command_output = ""
    history = _load_command_history()

    if request.method == 'POST':
        command = request.form['command']
        if command:
            history.insert(0, command) # Añadir al principio
            history = history[:20] # Mantener solo los últimos 20 comandos
            _save_command_history(history)

        try:
            # Ejecutar el comando y capturar la salida
            result = subprocess.run(command, shell=True, capture_output=True, text=True, check=True)
            command_output = result.stdout + result.stderr
        except subprocess.CalledProcessError as e:
            command_output = f"""Error al ejecutar el comando: {e}
{e.stdout}
{e.stderr}"""
        except Exception as e:
            command_output = f"Ocurrió un error inesperado: {e}"
    return render_template('run_command.html', command_output=command_output, command_history=history)

@app.route('/export_tasks')

def export_tasks():
    tareas = _cargar_tareas()
    si = io.StringIO()
    cw = csv.writer(si)
    
    # Escribir encabezados
    cw.writerow(["Descripcion", "Estado"])
    
    # Escribir datos
    for tarea in tareas:
        cw.writerow([tarea.get("descripcion", ""), tarea.get("estado", "")])
    
    output = make_response(si.getvalue())
    output.headers["Content-Disposition"] = "attachment; filename=tareas.csv"
    output.headers["Content-type"] = "text/csv"
    return output

@app.route('/export_projects')

def export_projects():
    projects = _cargar_proyectos()
    si = io.StringIO()
    cw = csv.writer(si)

    # Escribir encabezados
    cw.writerow(["Nombre", "Descripcion", "Ruta", "Estado", "Ultima Modificacion"])

    # Escribir datos
    for project in projects:
        cw.writerow([
            project.get("nombre", ""),
            project.get("descripcion", ""),
            project.get("ruta", ""),
            project.get("estado", ""),
            project.get("ultima_modificacion", "")
        ])

    output = make_response(si.getvalue())
    output.headers["Content-Disposition"] = "attachment; filename=proyectos.csv"
    output.headers["Content-type"] = "text/csv"
    return output

@app.route('/export_mcps')

def export_mcps():
    mcps = _get_custom_tools_data()
    si = io.StringIO()
    cw = csv.writer(si)

    # Escribir encabezados
    cw.writerow(["Nombre del Archivo"])

    # Escribir datos
    for mcp in mcps:
        cw.writerow([mcp])

    output = make_response(si.getvalue())
    output.headers["Content-Disposition"] = "attachment; filename=mcps.csv"
    output.headers["Content-type"] = "text/csv"
    return output

@app.route('/project_credentials_manager', methods=['GET', 'POST'])

def project_credentials_manager():
    credentials = _load_project_credentials()
    if request.method == 'POST':
        # Actualizar todas las credenciales enviadas en el formulario
        for key, value in request.form.items():
            credentials[key] = value
        try:
            _save_project_credentials(credentials)
            flash('Credenciales del proyecto guardadas correctamente.', 'success')
            return redirect(url_for('project_credentials_manager'))
        except (IOError, OSError) as e:
            app.logger.error(f"Error al guardar las credenciales del proyecto: {e}")
            flash('Error al guardar las credenciales del proyecto. Por favor, inténtalo de nuevo.', 'danger')
    return render_template('project_credentials_manager.html', credentials=credentials)

@app.route('/terminal')

def terminal():
    return render_template('terminal.html')

@app.route('/chatbot', methods=['GET', 'POST'])

def chatbot():
    chat_history = session.get('chat_history', [])

    if request.method == 'POST':
        user_message = request.form['user_message']
        chat_history.append({'role': 'user', 'parts': [{'text': user_message}]})

        try:
            # Enviar el historial completo a la API de Gemini
            gemini_response_text = _send_to_gemini_api(chat_history)
            chat_history.append({'role': 'model', 'parts': [{'text': gemini_response_text}]})
        except Exception as e:
            chat_history.append({'role': 'model', 'parts': [{'text': f"Lo siento, hubo un error al procesar tu solicitud: {e}"}]})

        session['chat_history'] = chat_history
    
    # Formatear el historial para la plantilla HTML
    display_history = []
    for msg in chat_history:
        sender = 'user' if msg['role'] == 'user' else 'gemini'
        display_history.append({'sender': sender, 'message': msg['parts'][0]['text']})

    return render_template('chatbot.html', chat_history=display_history)

@app.route('/kanban_tasks')

def kanban_tasks():
    all_tareas = _cargar_tareas()
    tasks_pendiente = [t for t in all_tareas if t.get('estado') == 'pendiente']
    tasks_en_progreso = [t for t in all_tareas if t.get('estado') == 'en_progreso']
    tasks_completada = [t for t in all_tareas if t.get('estado') == 'completada']
    return render_template('kanban_tasks.html',
                           tasks_pendiente=tasks_pendiente,
                           tasks_en_progreso=tasks_en_progreso,
                           tasks_completada=tasks_completada)

@app.route('/update_task_status', methods=['POST'])

def update_task_status():
    data = request.get_json()
    task_id = data.get('task_id') # Ya es un string UUID
    new_status = data.get('new_status')

    tareas = _cargar_tareas()
    for i, tarea in enumerate(tareas):
        if tarea.get('id') == task_id:
            tareas[i]['estado'] = new_status
            _guardar_tareas(tareas)
            socketio.emit('task_status_updated', {'task_id': task_id, 'new_status': new_status, 'description': tarea.get('descripcion', '')})
            return jsonify(success=True)
    return jsonify(success=False, message='Tarea no encontrada')

@app.route('/project_stats')

def project_stats():
    all_projects = _cargar_proyectos()

    # Calcular proyectos por estado
    project_status_counts = Counter(p.get('estado', 'desconocido') for p in all_projects)

    # Calcular proyectos por año de última modificación
    project_modification_years = []
    for p in all_projects:
        mod_date_str = p.get('ultima_modificacion')
        if mod_date_str:
            try:
                # Asumiendo formato 'YYYY-MM-DD HH:MM:SS'
                mod_year = datetime.strptime(mod_date_str.split(' ')[0], '%Y-%m-%d').year
                project_modification_years.append(str(mod_year))
            except ValueError:
                # Manejar fechas con formato incorrecto
                pass
    project_modification_counts = Counter(project_modification_years)

    return render_template('project_stats.html',
                           project_status_data=project_status_counts,
                           project_modification_data=project_modification_counts)

# --- Rutas de Estado del Sistema ---
@app.route('/system_status')

def system_status():
    status_checks = []

    # Archivos de configuración y datos
    files_to_check = {
        "Configuración del CLI": CONFIG_FILE,
        "Tareas": TAREAS_FILE,
        "Memoria de Contexto": CONTEXT_MEMORY_FILE,
        "Credenciales del Proyecto": PROJECT_CREDENTIALS_FILE,
        "Proyectos": PROYECTOS_FILE,
        "Historial de Comandos": COMMAND_HISTORY_FILE,
        "Usuarios (Autenticación)": USERS_FILE
    }

    for name, path in files_to_check.items():
        exists = os.path.exists(path)
        status_checks.append({
            "item": f"Archivo {name}",
            "status": "Existe ✅" if exists else "No existe ❌",
            "details": f"Ruta: {path}"
        })

    # Directorios de herramientas personalizadas y entornos virtuales
    dirs_to_check = {
        "Herramientas Personalizadas (MCP)": CUSTOM_TOOLS_DIR,
        "Entornos Virtuales": ENV_DIR
    }

    for name, path in dirs_to_check.items():
        exists = os.path.exists(path)
        is_dir = os.path.isdir(path)
        status_checks.append({
            "item": f"Directorio {name}",
            "status": "Existe ✅" if exists and is_dir else "No existe o no es un directorio ❌",
            "details": f"Ruta: {path}"
        })

    # Permisos de escritura (ejemplo: para archivos JSON)
    write_check_files = [
        CONFIG_FILE, TAREAS_FILE, CONTEXT_MEMORY_FILE, PROJECT_CREDENTIALS_FILE, COMMAND_HISTORY_FILE, USERS_FILE
    ]
    for path in write_check_files:
        can_write = os.access(path, os.W_OK) if os.path.exists(path) else False
        status_checks.append({
            "item": f"Permiso de escritura para {os.path.basename(path)}",
            "status": "Escribible ✅" if can_write else "No escribible ❌",
            "details": f"Ruta: {path}"
        })

    # Conectividad con la API de Gemini
    gemini_api_status = "Desconocido ❓"
    gemini_api_details = ""
    try:
        api_key = _get_gemini_api_key()
        # Intentar una llamada simple a la API para verificar la conectividad
        test_content = [{"parts": [{"text": "hello"}]}]
        _send_to_gemini_api(test_content) # No necesitamos la respuesta, solo verificar que no falle
        gemini_api_status = "Conectado ✅"
        gemini_api_details = "Conexión exitosa con la API de Gemini."
    except ValueError as e:
        gemini_api_status = "API Key no configurada ❌"
        gemini_api_details = str(e)
    except Exception as e:
        gemini_api_status = "Error de conexión ❌"
        gemini_api_details = str(e)
    
    status_checks.append({
        "item": "Conectividad con la API de Gemini",
        "status": gemini_api_status,
        "details": gemini_api_details
    })

    return render_template('system_status.html', status_checks=status_checks)

def _read_and_forward_output(sid, fd):
    while True:
        try:
            r, _, _ = select.select([fd], [], [], 0.1)
            if r:
                output = os.read(fd, 1024).decode('utf-8', errors='ignore')
                socketio.emit('output', {'output': output}, room=sid)
        except Exception as e:
            app.logger.error(f"Error reading from PTY for SID {sid}: {e}")
            break

@socketio.on('connect')
def handle_connect():
    sid = request.sid
    app.logger.info(f"Client connected: {sid}")
    master_fd, slave_fd = pty.openpty()
    p = subprocess.Popen(['bash'], stdin=slave_fd, stdout=slave_fd, stderr=slave_fd, preexec_fn=os.setsid)
    terminals[sid] = {'process': p, 'master_fd': master_fd}
    socketio.start_background_task(_read_and_forward_output, sid, master_fd)
    emit('output', {'output': '''Terminal connected. Type "exit" to close.\n'''})

@socketio.on('disconnect')
def handle_disconnect(sid):
    sid = request.sid
    app.logger.info(f"Client disconnected: {sid}")
    if sid in terminals:
        terminals[sid]['process'].terminate()
        os.close(terminals[sid]['master_fd'])
        del terminals[sid]


@socketio.on('input')
def handle_input(data):
    sid = request.sid
    if sid in terminals:
        os.write(terminals[sid]['master_fd'], data['input'].encode('utf-8'))

@app.errorhandler(500)
def internal_server_error(e):
    # Registrar el error para depuración
    app.logger.error(f"Error interno del servidor: {e}", exc_info=True)
    # Renderizar una página de error amigable para el usuario
    return render_template("500.html", error=str(e)), 500

if __name__ == '__main__':
    socketio.run(app, host='0.0.0.0', port=5000, debug=True)
