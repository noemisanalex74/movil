import csv
import io
import os
import uuid
from collections import Counter
from datetime import datetime

from dateparser.search import search_dates
from extensions import socketio
from flask import (
    Blueprint,
    Response,
    current_app,
    flash,
    jsonify,
    redirect,
    render_template,
    request,
    url_for,
)
from icalendar import Calendar, Event
from utils import _cargar_proyectos, _load_json, _save_json

tasks_bp = Blueprint("tasks", __name__)

# Define paths locally
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
TAREAS_FILE = os.path.join(BASE_DIR, "..", "instance", "tareas.json")


def _cargar_tareas():
    return _load_json(TAREAS_FILE, [])


def _guardar_tareas(tareas):
    _save_json(TAREAS_FILE, tareas)


@tasks_bp.route("/tasks")
def tasks_manager():
    """Renderiza la página del gestor de tareas. Los datos se cargan dinámicamente."""
    search_query = request.args.get("search", "").strip()
    return render_template("tasks_manager.html", search_query=search_query)


@tasks_bp.route("/task_add", methods=["GET", "POST"])
def task_add():
    all_projects = _cargar_proyectos()
    if request.method == "POST":
        descripcion = request.form["descripcion"]
        estado = request.form["estado"]
        proyecto = request.form["proyecto"]

        tareas = _cargar_tareas()
        nueva_tarea = {
            "id": str(uuid.uuid4()),
            "descripcion": descripcion,
            "estado": estado,
            "proyecto": proyecto,
            "fecha_modificacion": datetime.now().isoformat(),
        }
        tareas.append(nueva_tarea)
        _guardar_tareas(tareas)
        flash("Tarea añadida correctamente.", "success")
        return redirect(url_for("tasks.tasks_manager"))
    return render_template(
        "task_form.html",
        title="Añadir Nueva Tarea",
        task={"descripcion": "", "estado": "pendiente"},
        all_projects=all_projects,
    )


@tasks_bp.route("/task_edit/<task_id>", methods=["GET", "POST"])
def task_edit(task_id):
    all_projects = _cargar_proyectos()
    tareas = _cargar_tareas()
    task = next((t for t in tareas if t["id"] == task_id), None)

    if task is None:
        flash("Tarea no encontrada.", "danger")
        return redirect(url_for("tasks.tasks_manager"))

    if request.method == "POST":
        task["descripcion"] = request.form["descripcion"]
        task["estado"] = request.form["estado"]
        task["proyecto"] = request.form["proyecto"]
        task["fecha_modificacion"] = datetime.now().isoformat()
        _guardar_tareas(tareas)
        flash("Tarea actualizada correctamente.", "success")
        return redirect(url_for("tasks.tasks_manager"))

    return render_template(
        "task_form.html",
        title="Editar Tarea",
        task_id=task_id,
        task=task,
        all_projects=all_projects,
    )


@tasks_bp.route("/task_delete/<task_id>", methods=["GET"])
def task_delete(task_id):
    tareas = _cargar_tareas()
    tareas = [t for t in tareas if t.get("id") != task_id]
    _guardar_tareas(tareas)
    flash("Tarea eliminada correctamente.", "success")
    return redirect(url_for("tasks.tasks_manager"))


@tasks_bp.route("/kanban_tasks")
def kanban_tasks():
    all_tareas = _cargar_tareas()
    tasks_pendiente = [t for t in all_tareas if t.get("estado") == "pendiente"]
    tasks_en_progreso = [t for t in all_tareas if t.get("estado") == "en_progreso"]
    tasks_completada = [t for t in all_tareas if t.get("estado") == "completada"]
    return render_template(
        "kanban_tasks.html",
        tasks_pendiente=tasks_pendiente,
        tasks_en_progreso=tasks_en_progreso,
        tasks_completada=tasks_completada,
    )


@tasks_bp.route("/update_task_status", methods=["POST"])
def update_task_status():
    data = request.get_json()
    task_id = data.get("task_id")  # Ya es un string UUID
    new_status = data.get("new_status")

    tareas = _cargar_tareas()
    for i, tarea in enumerate(tareas):
        if tarea.get("id") == task_id:
            tareas[i]["estado"] = new_status
            _guardar_tareas(tareas)
            socketio.emit(
                "task_status_updated",
                {
                    "task_id": task_id,
                    "new_status": new_status,
                    "description": tarea.get("descripcion", ""),
                },
            )
            return jsonify(success=True)
    return jsonify(success=False, message="Tarea no encontrada")


@tasks_bp.route("/project_stats")
def project_stats():
    all_projects = _cargar_proyectos()
    all_tareas = _cargar_tareas()

    # Proyectos por estado
    project_status_counts = Counter(
        p.get("estado", "desconocido") for p in all_projects
    )

    # Proyectos por año de última modificación
    project_modification_years = []
    for p in all_projects:
        mod_date_str = p.get("ultima_modificacion")
        if mod_date_str:
            try:
                mod_year = datetime.strptime(
                    mod_date_str.split(" ")[0], "%Y-%m-%d"
                ).year
                project_modification_years.append(str(mod_year))
            except ValueError:
                pass
    project_modification_counts = Counter(project_modification_years)

    # Tareas por estado
    task_status_counts = Counter(t.get("estado", "desconocido") for t in all_tareas)

    return render_template(
        "project_stats.html",
        project_status_data=project_status_counts,
        project_modification_data=project_modification_counts,
        task_status_data=task_status_counts,
    )


@tasks_bp.route("/empresas_manager")
def empresas_manager():
    """Renderiza la página del gestor de empresas. Los datos se cargan dinámicamente."""
    return render_template("empresas_manager.html")


@tasks_bp.route("/project_add", methods=["GET"])
def project_add():
    return render_template(
        "project_form.html", title="Añadir Nuevo Proyecto", project={}
    )

@tasks_bp.route("/project_edit/<project_id>")
def project_edit(project_id):
    return render_template(
        "project_form.html", title="Editar Proyecto", project_id=project_id
    )


@tasks_bp.route("/system_status")
def system_status():
    import sys

    import flask
    from extensions import db

    status_checks = []

    # Python version
    status_checks.append(
        {"item": "Python Version", "status": sys.version, "details": ""}
    )

    # Flask version
    status_checks.append(
        {"item": "Flask Version", "status": flask.__version__, "details": ""}
    )

    # Database status
    try:
        db.session.execute("SELECT 1")
        db_status = "Conectado ✅"
        db_details = ""
    except Exception as e:
        db_status = "Error de conexión ❌"
        db_details = str(e)

    status_checks.append(
        {"item": "Database Status", "status": db_status, "details": db_details}
    )

    return render_template("system_status.html", status_checks=status_checks)


@tasks_bp.route("/export_tasks")
def export_tasks():
    tareas = _cargar_tareas()
    output = io.StringIO()
    writer = csv.writer(output)

    # Write header
    writer.writerow(
        ["ID", "Descripcion", "Estado", "Proyecto", "Fecha de Modificacion"]
    )

    # Write data
    for tarea in tareas:
        writer.writerow(
            [
                tarea.get("id", ""),
                tarea.get("descripcion", ""),
                tarea.get("estado", ""),
                tarea.get("proyecto", ""),
                tarea.get("fecha_modificacion", ""),
            ]
        )

    output.seek(0)

    return Response(
        output,
        mimetype="text/csv",
        headers={"Content-Disposition": "attachment;filename=tareas.csv"},
    )


@tasks_bp.route("/export_tasks.ics")
def export_tasks_ics():
    """Generates an iCalendar file for tasks with a due date."""
    tareas = _cargar_tareas()
    tasks_with_due_date = [t for t in tareas if t.get("fecha_vencimiento")]

    cal = Calendar()
    cal.add('prodid', '-//AGP Dashboard//Tasks//EN')
    cal.add('version', '2.0')

    for task in tasks_with_due_date:
        try:
            due_date = datetime.fromisoformat(task["fecha_vencimiento"])
            event = Event()
            event.add('summary', task["descripcion"])
            event.add('dtstart', due_date)
            event.add('dtend', due_date)
            event.add('uid', f"{task['id']}@agp-dashboard.local")
            event.add('dtstamp', datetime.now())
            cal.add_component(event)
        except (ValueError, TypeError):
            continue # Skip tasks with invalid date format

    return Response(
        cal.to_ical(),
        mimetype="text/calendar",
        headers={"Content-Disposition": "attachment;filename=tareas.ics"},
    )


@tasks_bp.route("/analytics")
def analytics():
    """Processes task data and renders the analytics page."""
    tareas = _cargar_tareas()
    completed_tasks = [
        t for t in tareas
        if t.get("estado") == "completada" and t.get("fecha_modificacion")
    ]

    # --- Stats for last 30 days ---
    from collections import defaultdict
    from datetime import timedelta

    last_30_days = defaultdict(int)
    today = datetime.now().date()
    for i in range(30):
        day = today - timedelta(days=i)
        last_30_days[day.strftime("%Y-%m-%d")] = 0

    for task in completed_tasks:
        mod_date = datetime.fromisoformat(task["fecha_modificacion"]).date()
        if (today - mod_date).days < 30:
            last_30_days[mod_date.strftime("%Y-%m-%d")] += 1

    # Sort by date for the chart
    last_30_days_sorted = sorted(last_30_days.items())

    # --- Stats by day of the week ---
    day_of_week_counts = defaultdict(int)
    day_names = [
        "Lunes", "Martes", "Miércoles", "Jueves", "Viernes", "Sábado", "Domingo"
    ]
    for task in completed_tasks:
        mod_date = datetime.fromisoformat(task["fecha_modificacion"])
        day_of_week_counts[mod_date.weekday()] += 1

    day_of_week_data = [day_of_week_counts[i] for i in range(7)]

    stats = {
        "total_completed": len(completed_tasks),
        "last_30_days_labels": [item[0] for item in last_30_days_sorted],
        "last_30_days_values": [item[1] for item in last_30_days_sorted],
        "day_of_week_labels": day_names,
        "day_of_week_values": day_of_week_data
    }

    return render_template("analytics.html", stats=stats)


@tasks_bp.route("/voice_task", methods=["POST"])
def voice_task():
    data = request.get_json()
    if not data or "text" not in data:
        return jsonify(status="error", message="No text provided"), 400

    full_text = data["text"]
    found_dates = search_dates(full_text, languages=['es'])
    clean_description = full_text
    due_date = None

    if found_dates:
        date_str, parsed_date = found_dates[0]
        due_date = parsed_date.isoformat()
        temp_description = full_text.replace(date_str, '', 1).strip()
        if temp_description:
            clean_description = temp_description

    tareas = _cargar_tareas()

    nueva_tarea = {
        "id": str(uuid.uuid4()),
        "descripcion": clean_description,
        "estado": "pendiente",
        "proyecto": "",
        "fecha_modificacion": datetime.now().isoformat(),
        "fecha_vencimiento": due_date
    }

    tareas.append(nueva_tarea)

    try:
        _guardar_tareas(tareas)
        socketio.emit("new_task", {"descripcion": nueva_tarea["descripcion"]})
        notification_content = f'{clean_description}'
        if due_date:
            try:
                formatted_due_date = datetime.fromisoformat(due_date).strftime(
                    '%d/%m %H:%M'
                )
                notification_content += f' - Vence: {formatted_due_date}'
            except (ValueError, TypeError):
                pass # Ignore formatting errors if date is invalid

        os.system(
            f'termux-notification --title "Tarea creada por voz" '
            f'--content "{notification_content}"'
        )
        flash("Tarea añadida por voz correctamente.", "success")
        return jsonify(status="success", message="Task added successfully")

    except (IOError, OSError) as e:
        current_app.logger.error(f"Error al añadir tarea por voz: {e}")
        return jsonify(status="error", message="Failed to save task"), 500
