import eventlet

eventlet.monkey_patch()
import json
import os
import subprocess
import sys
from datetime import datetime

import click
import extensions
from flask import Flask, jsonify, redirect, url_for
from flask.cli import with_appcontext
from flask_compress import Compress
from playbook_executor import PlaybookExecutor
from utils import _cargar_proyectos, get_dashboard_stats


def broadcast_device_status():
    """
    Fetches device status from Termux:API and broadcasts it via Socket.IO.
    This job is executed in an application context provided by Flask-APScheduler.
    """
    from flask import current_app
    try:
        battery_result = subprocess.run(
            ['termux-battery-status'],
            capture_output=True, text=True, check=True, timeout=5
        )
        battery_data = json.loads(battery_result.stdout)
        extensions.socketio.emit(
            'agent_battery_update',
            {'battery': battery_data},
            namespace='/agent'
        )
    except (
        subprocess.CalledProcessError,
        FileNotFoundError,
        json.JSONDecodeError,
        subprocess.TimeoutExpired,
    ) as e:
        current_app.logger.warning("Could not fetch Termux device status", error=str(e))

@click.command(name="seed_db")
@with_appcontext
def seed_db():
    """Crea los datos iniciales para la base de datos, como el usuario admin."""
    from extensions import db
    from models import User

    if User.query.filter_by(username="admin").first() is None:
        print("Creando usuario admin...")
        admin_user = User(username="admin")
        admin_user.set_password("password")
        db.session.add(admin_user)
        db.session.commit()
        print("Usuario 'admin' con contraseña 'password' creado.")
    else:
        print("El usuario admin ya existe.")


@click.command(name="reset-admin-password")
@click.argument("new_password")
@with_appcontext
def reset_admin_password(new_password):
    """Resets the admin user's password."""
    from extensions import db
    from models import User

    admin_user = User.query.filter_by(username="admin").first()
    if admin_user:
        admin_user.set_password(new_password)
        db.session.commit()
        print("Admin password has been reset successfully.")
    else:
        print("Admin user not found. Please run 'seed_db' first.")

@click.command(name="import-projects")
@with_appcontext
def import_projects():
    """Imports projects from the JSON file into the database."""
    from extensions import db
    from models import Project

    print("Iniciando importación de proyectos desde JSON...")
    projects_from_json = _cargar_proyectos()

    if not projects_from_json:
        print(
            "No se encontraron proyectos en el archivo JSON. "
            "No hay nada que importar."
        )
        return

    imported_count = 0
    skipped_count = 0
    for project_data in projects_from_json:
        project_id = project_data.get('id')
        if not project_id:
            print(f"Omitiendo registro por falta de ID: {project_data.get('name')}")
            skipped_count += 1
            continue

        exists = Project.query.get(project_id)
        if exists:
            # print(f"Proyecto '{project_data.get('name')}' ya existe. Omitiendo.")
            skipped_count += 1
            continue

        # Convertir fecha de string a objeto datetime
        last_modified_str = project_data.get('ultima_modificacion')
        last_modified_dt = None
        if last_modified_str:
            try:
                last_modified_dt = datetime.fromisoformat(last_modified_str)
            except (ValueError, TypeError):
                print(
                    f"Advertencia: Formato de fecha inválido para el proyecto "
                    f"{project_id}. Se usará la fecha actual."
                )
                last_modified_dt = datetime.now()

        new_project = Project(
            id=project_id,
            name=project_data.get('nombre'),
            description=project_data.get('descripcion'),
            path=project_data.get('ruta'),
            status=project_data.get('estado', 'nuevo'),
            last_modified=last_modified_dt
        )
        db.session.add(new_project)
        imported_count += 1
        print(f"Importando proyecto: {new_project.name}")

    if imported_count > 0:
        db.session.commit()
        print(f"\n¡Éxito! Se importaron {imported_count} nuevos proyectos.")
    else:
        print("\nNo se importaron nuevos proyectos.")

    if skipped_count > 0:
        print(f"Se omitieron {skipped_count} proyectos que ya existían o no tenían ID.")

def create_app() -> Flask:
    """
    Application factory to create and configure the Flask application.
    """
    # Define a stable instance path outside the project folder to avoid reloader issues
    instance_path = os.path.abspath(
        os.path.join(os.path.dirname(__file__), "..", "agp_dashboard_instance")
    )
    app = Flask(
        __name__,
        instance_path=instance_path,
        instance_relative_config=True,
        template_folder="templates",
    )

    # --- Structured Logging Configuration ---
    import logging
    from logging.handlers import RotatingFileHandler

    import structlog
    from structlog.processors import JSONRenderer, TimeStamper, add_log_level

    log_file_path = os.path.join(app.instance_path, 'app.log')
    os.makedirs(app.instance_path, exist_ok=True) # Ensure instance path exists for logs

    # Configure standard logging handlers first
    file_handler = RotatingFileHandler(log_file_path, maxBytes=10000000, backupCount=5)
    # structlog will handle formatting, so just pass the message through
    file_handler.setFormatter(logging.Formatter("%(message)s"))
    file_handler.setLevel(logging.INFO)

    stream_handler = logging.StreamHandler(sys.stdout)
    # structlog will handle formatting, so just pass the message through
    stream_handler.setFormatter(logging.Formatter("%(message)s"))
    stream_handler.setLevel(logging.INFO)

    # Add handlers to Flask's app.logger
    app.logger.addHandler(file_handler)
    app.logger.addHandler(stream_handler)
    app.logger.setLevel(logging.INFO) # Set level for app.logger

    structlog.configure(
        processors=[
            add_log_level,
            TimeStamper(fmt="iso"),
            JSONRenderer(),
        ],
        wrapper_class=structlog.make_filtering_bound_logger(logging.INFO),
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        cache_logger_on_first_use=True,
    )

    # Replace Flask's default logger with the structured logger
    # This step is crucial for structlog to take over
    app.logger = structlog.get_logger()
    app.logger.info("Logging configured for Flask application with rotation.")
    # --- End of Structured Logging Configuration ---

    app.config["TEMPLATES_AUTO_RELOAD"] = True
    Compress(app)

    # Load the instance config, if it exists, when not testing
    app.config.from_pyfile("config.py", silent=True)

    # After loading config, get the absolute DB path
    db_uri = app.config.get("SQLALCHEMY_DATABASE_URI")
    if not db_uri:
        raise ValueError("SQLALCHEMY_DATABASE_URI not set in config.py")

    # Scheduler Configuration - USE THE SAME DB as the main app
    app.config["SCHEDULER_JOBSTORES"] = {
        "default": {"type": "sqlalchemy", "url": db_uri}
    }
    app.config["SCHEDULER_API_ENABLED"] = True

    app.config["BABEL_DEFAULT_LOCALE"] = "es"
    app.config["BABEL_DEFAULT_TIMEZONE"] = "UTC"

    # Ensure the instance folder exists
    try:
        os.makedirs(app.instance_path)
    except OSError:
        pass

    # Initialize extensions
    extensions.init_app(app)
    app.socketio = extensions.socketio # Make socketio accessible via app.socketio
    extensions.migrate.init_app(app, extensions.db)

    # --- Auto-login feature for admin user ---
    @app.before_request
    def auto_login_admin():
        from flask import request
        from flask_login import current_user, login_user
        from models import User

        # Evitar el auto-login en la ruta de logout para permitir la desconexión
        if request.endpoint and 'logout' in request.endpoint:
            return

        if not current_user.is_authenticated:
            admin_user = User.query.filter_by(username="admin").first()
            if admin_user:
                login_user(admin_user)

    # Store connected agents (this might be better in a dedicated module)
    app.connected_agents = {}

    # Initialize Playbook Executor
    app.playbook_executor = PlaybookExecutor(extensions.socketio, app.connected_agents)

    # Register the agent Socket.IO namespace
    # register_agent_namespace(extensions.socketio, app.playbook_executor)

    # --- Swagger UI Configuration ---
    from flask_swagger_ui import get_swaggerui_blueprint

    SWAGGER_URL = "/api/docs"
    API_URL = "/static/swagger.json"

    swaggerui_blueprint = get_swaggerui_blueprint(
        SWAGGER_URL, API_URL, config={"app_name": "AGP Dashboard API"}
    )
    app.register_blueprint(swaggerui_blueprint)
    # --- End of Swagger UI Configuration ---

    # Register Blueprints
    from blueprints.agents import agents_bp
    from blueprints.api import api_bp
    from blueprints.api.v1 import api_v1_bp  # Import for API v1
    from blueprints.assistant import assistant_bp  # Import new blueprint
    from blueprints.contacts import contacts_bp
    from blueprints.culinary_studio import culinary_studio_bp
    from blueprints.enterprise import enterprise_bp
    from blueprints.github import github_bp
    from blueprints.google_auth import google_auth_bp
    from blueprints.local_execution import local_execution_bp
    from blueprints.location import location_bp
    from blueprints.mcp import mcp_bp
    from blueprints.notifications import notifications_bp
    from blueprints.playbooks import playbooks_bp
    from blueprints.projects import projects_bp
    from blueprints.scheduler import scheduler_bp
    from blueprints.settings import settings_bp
    from blueprints.social_media import social_media_bp
    from blueprints.system import system_bp
    from blueprints.tasks import tasks_bp
    from blueprints.vault import vault_bp
    from blueprints.visual_notes import visual_notes_bp

    app.register_blueprint(agents_bp)
    app.register_blueprint(enterprise_bp)
    app.register_blueprint(github_bp)
    app.register_blueprint(google_auth_bp)
    app.register_blueprint(local_execution_bp)
    app.register_blueprint(mcp_bp)
    app.register_blueprint(notifications_bp)
    app.register_blueprint(playbooks_bp)
    app.register_blueprint(scheduler_bp)
    app.register_blueprint(settings_bp)
    app.register_blueprint(social_media_bp)
    app.register_blueprint(system_bp)
    app.register_blueprint(tasks_bp)
    app.register_blueprint(location_bp)
    app.register_blueprint(visual_notes_bp)
    app.register_blueprint(contacts_bp)
    app.register_blueprint(vault_bp)
    app.register_blueprint(assistant_bp) # Register new blueprint
    app.register_blueprint(projects_bp)
    app.register_blueprint(api_bp) # Main API blueprint
    app.register_blueprint(api_v1_bp) # Register API v1
    app.register_blueprint(culinary_studio_bp)

    if not app.config.get("TESTING"):
        from blueprints.gemini_cli import gemini_cli_bp
        from blueprints.threed_lab import threed_lab_bp

        app.register_blueprint(gemini_cli_bp)
        app.register_blueprint(threed_lab_bp)

    # @extensions.socketio.on("join_room")
    # def handle_join_room_event(data):
    #     from flask_login import current_user

    #     if current_user.is_authenticated:
    #         from flask import request
    #         from flask_socketio import join_room

    #         join_room(f"user_{current_user.id}")
    #         print(
    #             f"User {current_user.username} joined room "
    #             f"user_{current_user.id} with sid {request.sid}"
    #         )

    # API route for dashboard stats
    @app.route("/api/dashboard_stats")
    def api_dashboard_stats():
        # NOTE: AgentTask and CustomTool have been removed.
        # This function needs to be updated with new stats sources.
        stats = get_dashboard_stats(extensions.db, None, None)
        return jsonify(stats)

    # Register CLI commands
    app.cli.add_command(seed_db)
    app.cli.add_command(reset_admin_password)

    @app.context_processor
    def inject_menu():
        """Injects the dynamic menu structure into all templates."""
        main_menu = [
            {
                "type": "link",
                "name": "Resumen",
                "url": "dashboard",
                "icon": "bi-house-door-fill",
            },
            {
                "type": "submenu",
                "name": "Gestión",
                "id": "gestion-submenu",
                "icon": "bi-kanban-fill",
                "items": [
                    {
                        "name": "Proyectos",
                        "url": "projects.projects_manager",
                        "icon": "bi-folder-check",
                    },
                    {
                        "name": "Tareas",
                        "url": "tasks.tasks_manager",
                        "icon": "bi-list-check",
                    },
                    {"name": "MCPs", "url": "mcp.mcp_manager", "icon": "bi-tools"},
                ],
            },
            {
                "type": "submenu",
                "name": "IA Tools",
                "id": "ia-tools-submenu",
                "icon": "bi-robot",
                "items": [
                    {
                        "name": "Laboratorio 3D",
                        "url": "threed_lab.lab",
                        "icon": "bi-box-fill",
                    },
                    {
                        "name": "Galería de Modelos",
                        "url": "threed_lab.gallery",
                        "icon": "bi-collection-fill",
                    },
                    {
                        "name": "Visor AR",
                        "url": "ar_viewer",
                        "icon": "bi-badge-ar-fill",
                    },
                    {
                        "name": "Estudio Culinario",
                        "url": "culinary_studio.studio_page",
                        "icon": "bi-image-fill",
                    },
                    {
                        "name": "Carga de Material",
                        "url": "threed_lab.upload",
                        "icon": "bi-cloud-arrow-up-fill",
                    }
                ],
            },
            {
                "type": "submenu",
                "name": "SYSTEM",
                "id": "system-submenu",
                "icon": "bi-hdd-stack-fill",
                "items": [
                    {
                        "name": "Ejecución Local",
                        "url": "local_execution.execution_page",
                        "icon": "bi-terminal-fill",
                    },
                    {
                        "name": "Notificaciones Termux",
                        "url": "notifications.termux_notify",
                        "icon": "bi-phone-vibrate-fill",
                    },
                    {
                        "name": "Ajustes",
                        "url": "settings.settings_manager",
                        "icon": "bi-gear-wide-connected",
                    },
                    {
                        "name": "Gestor de Secretos",
                        "url": "vault.vault_manager",
                        "icon": "bi-key-fill",
                    },
                    {
                        "name": "Copias de Seguridad",
                        "url": "system.backup_page",
                        "icon": "bi-database-down",
                    },
                    {
                        "name": "Visor de Logs",
                        "url": "logs_viewer",
                        "icon": "bi-file-earmark-text-fill",
                    },
                ],
            },
        ]
        return dict(main_menu=main_menu)

    @app.route("/logs_viewer")
    def logs_viewer():
        import os

        from flask import current_app, render_template
        log_file_path = os.path.join(current_app.instance_path, 'app.log')
        log_content = "No se pudo leer el archivo de logs."
        try:
            with open(log_file_path, 'r', encoding='utf-8') as f:
                log_content = f.read()
        except Exception as e:
            current_app.logger.error(f"Error al leer el archivo de logs: {e}")
        return render_template("logs_viewer.html", log_content=log_content)

    @app.route("/ar_viewer")
    def ar_viewer():
        from flask import current_app, render_template
        models_dir = os.path.join(current_app.static_folder, 'models')
        model_files = []
        try:
            if os.path.exists(models_dir):
                model_files = [f for f in os.listdir(models_dir) if f.endswith('.glb')]
            else:
                current_app.logger.warning(
                    f"El directorio de modelos no fue encontrado en: {models_dir}"
                )
        except Exception as e:
            current_app.logger.error(f"Error al leer el directorio de modelos: {e}")

        return render_template(
            'ar_viewer.html',
            title="Visor de Realidad Aumentada",
            model_files=model_files
        )


    @app.route("/")
    def spatial_dashboard():
        from flask import render_template
        return render_template("spatial_dashboard.html")

    @app.route("/summary")
    def dashboard():
        from flask import render_template
        # The data is now fetched asynchronously by the client
        return render_template("dashboard.html")

    @app.route("/search")
    def search():
        from flask import render_template, request
        from models import Agent
        from utils import _cargar_proyectos, _cargar_tareas

        query = request.args.get("q", "").strip()
        if not query:
            return redirect(url_for("dashboard"))

        # Convert query to lowercase for case-insensitive search
        l_query = query.lower()

        # Search in Tareas
        all_tareas = _cargar_tareas()
        res_tareas = [
            t for t in all_tareas if l_query in t.get("descripcion", "").lower()
        ]

        # Search in Proyectos
        all_proyectos = _cargar_proyectos()
        res_proyectos = [
            p
            for p in all_proyectos
            if l_query in p.get("nombre", "").lower()
            or l_query in p.get("descripcion", "").lower()
        ]

        # Search in Agents
        res_agents = Agent.query.filter(
            Agent.name.ilike(f"%{l_query}%")
            | Agent.description.ilike(f"%{l_query}%")
            | Agent.location.ilike(f"%{l_query}%")
        ).all()

        results = {
            "tareas": res_tareas,
            "proyectos": res_proyectos,
            "agents": res_agents,
        }

        return render_template("search_results.html", query=query, results=results)

    if not app.config.get("TESTING"):
        # Add the background job to the scheduler
        # Use a string reference to the function to avoid import issues with CLI commands
        if not extensions.scheduler.get_job('device_status_job'):
            extensions.scheduler.add_job(
                id='device_status_job',
                func='app:broadcast_device_status',
                trigger='interval',
                seconds=30,
                replace_existing=True
            )

    return app


if __name__ == "__main__":
    app = create_app()
    # Disable the reloader permanently as it's incompatible with the environment
    extensions.socketio.run(
        app, host="0.0.0.0", port=5000, debug=True, use_reloader=False
    )
