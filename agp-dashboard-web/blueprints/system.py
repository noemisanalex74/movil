import io
import os
import zipfile
from datetime import datetime

from flask import (
    Blueprint,
    current_app,
    flash,
    redirect,
    render_template,
    request,
    send_file,
    url_for,
)

system_bp = Blueprint("system", __name__, url_prefix="/system")


@system_bp.route("/backup")
def backup_page():
    """Muestra la página de gestión de copias de seguridad."""
    return render_template("system/backup.html")


@system_bp.route("/backup/create")
def create_backup():
    """Crea un archivo ZIP con los datos importantes y lo envía para descarga."""
    memory_file = io.BytesIO()
    base_path = current_app.root_path

    paths_to_backup = {
        os.path.join(base_path, "instance"): "instance",
        os.path.join(base_path, "playbooks"): "playbooks",
    }

    with zipfile.ZipFile(memory_file, "w", zipfile.ZIP_DEFLATED) as zf:
        for path, arc_dir in paths_to_backup.items():
            if not os.path.exists(path):
                continue
            if os.path.isfile(path):
                zf.write(path, os.path.join(arc_dir, os.path.basename(path)))
            elif os.path.isdir(path):
                for root, _, files in os.walk(path):
                    for file in files:
                        file_path = os.path.join(root, file)
                        archive_name = os.path.join(
                            arc_dir, os.path.relpath(file_path, path)
                        )
                        zf.write(file_path, archive_name)

    memory_file.seek(0)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"agp_dashboard_backup_{timestamp}.zip"

    return send_file(
        memory_file,
        download_name=filename,
        as_attachment=True,
        mimetype="application/zip",
    )


@system_bp.route("/backup/restore", methods=["POST"])
def restore_backup():
    """Restaura la aplicación desde un archivo de backup."""
    if "backup_file" not in request.files:
        flash("No se encontró el archivo en la petición.", "danger")
        return redirect(url_for(".backup_page"))

    file = request.files["backup_file"]
    if file.filename == "" or not file.filename.endswith(".zip"):
        flash("Por favor, selecciona un archivo .zip válido.", "danger")
        return redirect(url_for(".backup_page"))

    try:
        base_path = current_app.root_path
        with zipfile.ZipFile(file, "r") as zf:
            # Extraer y reemplazar los directorios de datos
            # ATENCIÓN: Esto es destructivo.
            zf.extractall(path=base_path)

        flash(
            "Copia de seguridad restaurada con éxito. Por favor, REINICIA el servidor para aplicar los cambios.",
            "success",
        )
    except Exception as e:
        flash(f"Ocurrió un error durante la restauración: {e}", "danger")

    return redirect(url_for(".backup_page"))
