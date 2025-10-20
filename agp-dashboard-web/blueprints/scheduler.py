import os

from extensions import scheduler
from flask import (
    Blueprint,
    current_app,
    flash,
    redirect,
    render_template,
    request,
    url_for,
)

from .notifications import create_notification

scheduler_bp = Blueprint("scheduler", __name__, template_folder="../templates")

PLAYBOOKS_DIR = "playbooks"


def run_playbook_job(playbook_id, agent_id):
    """Función que será ejecutada por el scheduler."""
    with scheduler.app.app_context():
        playbook_path = os.path.join(PLAYBOOKS_DIR, playbook_id)
        log = current_app.logger
        log.info(
            f"Executing scheduled playbook '{playbook_path}' on agent '{agent_id}'."
        )

        success = False
        error_message = ""
        try:
            # Note: run_playbook_from_file now starts a background task
            current_app.playbook_executor.run_playbook_from_file(
                playbook_path, agent_id
            )
            success = True
            log.info(f"Successfully scheduled playbook execution for: {playbook_id}")
        except Exception as e:
            error_message = str(e)
            log.error(f"Error scheduling playbook execution for {playbook_id}: {e}")

        # Crear notificación para el admin (user_id=1)
        if success:
            message = f"Playbook '{playbook_id}' programado para ejecución."
        else:
            message = (
                f"Falló la programación del playbook '{playbook_id}': {error_message}"
            )

        # This should be done in a way that doesn't require a request context if run purely in background
        # For now, this will work as it runs within app_context
        create_notification(user_id=1, message=message)


@scheduler_bp.route("/scheduler")
def scheduler_manager():
    jobs = []
    try:
        jobs = scheduler.get_jobs()
    except Exception as e:
        flash(f"No se pudo conectar con el job store del planificador: {e}", "danger")
        current_app.logger.error(f"Could not connect to scheduler job store: {e}")
    return render_template("scheduled_jobs_manager.html", jobs=jobs)


@scheduler_bp.route("/scheduler/add", methods=["GET", "POST"])
def add_job_route():
    if request.method == "POST":
        job_id = request.form.get("job_id")
        job_name = request.form.get("job_name")
        playbook_id = request.form.get("playbook_id")
        agent_id = request.form.get("agent_id")
        trigger_type = request.form.get("trigger_type")

        if not all([job_id, job_name, playbook_id, agent_id, trigger_type]):
            flash("Todos los campos son requeridos.", "danger")
            # Re-populate form for GET request
            return redirect(url_for(".add_job_route"))

        try:
            trigger_args = {}
            if trigger_type == "interval":
                trigger_args["minutes"] = int(request.form.get("interval_minutes"))
            elif trigger_type == "cron":
                trigger_args["day_of_week"] = request.form.get("cron_day_of_week")
                trigger_args["hour"] = request.form.get("cron_hour")
                trigger_args["minute"] = request.form.get("cron_minute")

            scheduler.add_job(
                id=job_id,
                name=job_name,
                func=run_playbook_job,
                args=[playbook_id, agent_id],  # Pass both playbook_id and agent_id
                trigger=trigger_type,
                replace_existing=True,
                **trigger_args,
            )
            flash(f"Tarea '{job_name}' programada exitosamente.", "success")
            return redirect(url_for(".scheduler_manager"))
        except Exception as e:
            flash(f"Error al programar la tarea: {e}", "danger")

    # Para el método GET
    playbooks = []
    try:
        playbook_files = os.listdir(PLAYBOOKS_DIR)
        for p_file in playbook_files:
            if p_file.endswith((".yml", ".yaml")):
                playbooks.append({"id": p_file, "name": p_file})
    except FileNotFoundError:
        flash(
            f"El directorio de playbooks '{PLAYBOOKS_DIR}' no fue encontrado.",
            "warning",
        )

    connected_agents = list(current_app.connected_agents.values())

    return render_template(
        "schedule_playbook.html", playbooks=playbooks, agents=connected_agents
    )


@scheduler_bp.route("/scheduler/delete/<job_id>", methods=["POST"])
def delete_job_route(job_id):
    try:
        scheduler.remove_job(job_id)
        flash(f"Tarea '{job_id}' eliminada exitosamente.", "success")
    except Exception as e:
        flash(f"Error al eliminar la tarea: {e}", "danger")
    return redirect(url_for(".scheduler_manager"))
