# agp-dashboard-web/blueprints/threed_lab.py
import json
import os
import time
from threading import Thread
import io

import requests
from flask import (
    Blueprint,
    current_app,
    flash,
    redirect,
    render_template,
    request,
    url_for,
)
from google.oauth2.credentials import Credentials

# Conditional import for googleapiclient
if not os.environ.get("FLASK_TESTING"):
    from googleapiclient.discovery import build
    from googleapiclient.errors import HttpError
    from googleapiclient.http import MediaFileUpload
else:
    # Dummy functions/classes for when googleapiclient is not installed or in testing mode
    def build(*args, **kwargs):
        print("Mock googleapiclient.discovery.build called (FLASK_TESTING is True)")
        return MockDriveService()

    class MockDriveService:
        def files(self):
            return MockFiles()

    class MockFiles:
        def list(self, *args, **kwargs):
            return MockExecute()

        def create(self, *args, **kwargs):
            return MockExecute()

    class MockExecute:
        def execute(self):
            print("Mock execute called (FLASK_TESTING is True)")
            return {"files": []}  # Return empty list for file listings

    class HttpError(Exception):
        pass  # Define a dummy HttpError

    class MediaFileUpload:
        def __init__(self, *args, **kwargs):
            pass  # Dummy constructor

from models import Setting
from werkzeug.utils import secure_filename
from extensions import socketio

threed_lab_bp = Blueprint("threed_lab", __name__, url_prefix="/3d-lab")

# --- Rutas de Google Drive --- #


def get_drive_service():
    """Obtiene el objeto de servicio de Google Drive API o None si no está autenticado/configurado."""
    client_id_setting = Setting.query.filter_by(key="GOOGLE_CLIENT_ID").first()
    client_secret_setting = Setting.query.filter_by(key="GOOGLE_CLIENT_SECRET").first()
    if not (
        client_id_setting
        and client_id_setting.value
        and client_secret_setting
        and client_secret_setting.value
    ):
        return None, "config_missing"

    google_creds_setting = Setting.query.filter_by(key="GOOGLE_CREDENTIALS").first()
    if not google_creds_setting or not google_creds_setting.value:
        return None, "not_authenticated"

    try:
        creds_json = json.loads(google_creds_setting.value)
        creds = Credentials.from_authorized_user_info(creds_json)
        service = build("drive", "v3", credentials=creds)
        return service, "authenticated"
    except HttpError as error:
        flash(f"Ocurrió un error con la API de Google: {error}", "danger")
        return None, "not_authenticated"  # Las credenciales podrían haber expirado
    except Exception as e:
        flash(f"Ocurrió un error inesperado: {e}", "danger")
        return None, "not_authenticated"


def find_or_create_folder(service, folder_name, parent_id=None):
    """Busca una carpeta por nombre, si no existe, la crea."""
    q = f"mimeType='application/vnd.google-apps.folder' and name='{folder_name}'"
    if parent_id:
        q += f" and '{parent_id}' in parents"

    response = (
        service.files().list(q=q, spaces="drive", fields="files(id, name)").execute()
    )
    folders = response.get("files", [])

    if folders:
        return folders[0].get("id")
    else:
        file_metadata = {
            "name": folder_name,
            "mimeType": "application/vnd.google-apps.folder",
        }
        if parent_id:
            file_metadata["parents"] = [parent_id]
        folder = service.files().create(body=file_metadata, fields="id").execute()
        return folder.get("id")


@threed_lab_bp.route("/lab_dashboard", methods=["GET", "POST"])
def lab_dashboard():
    service, auth_status = get_drive_service()

    if auth_status == "config_missing":
        return render_template("threed_lab.html", config_missing=True)
    elif auth_status == "not_authenticated":
        return render_template("threed_lab.html", is_authenticated=False)

    # --- Lógica POST para subir archivos a Google Drive ---
    if request.method == "POST":
        if (
            "image_file" not in request.files
            or request.files["image_file"].filename == ""
        ):
            flash("No se seleccionó ningún archivo de imagen.", "danger")
            return redirect(request.url)

        file = request.files["image_file"]
        model_name = request.form.get("model_name", secure_filename(file.filename))

        try:
            # 1. Encontrar o crear la carpeta principal "Objetos3D"
            parent_folder_id = find_or_create_folder(service, "Objetos3D")
            if not parent_folder_id:
                flash(
                    'No se pudo encontrar o crear la carpeta "Objetos3D" en Google Drive.',
                    "danger",
                )
                return redirect(request.url)

            # 2. Encontrar o crear la subcarpeta "Entrada"
            input_folder_id = find_or_create_folder(
                service, "Entrada", parent_folder_id
            )
            if not input_folder_id:
                flash(
                    'No se pudo encontrar o crear la carpeta "Entrada" en Google Drive.',
                    "danger",
                )
                return redirect(request.url)

            # 3. Subir el archivo de imagen
            file_metadata = {
                "name": model_name,  # Usar el nombre del modelo como nombre del archivo
                "parents": [input_folder_id],
            }
            media = MediaFileUpload(file.stream, mimetype=file.mimetype, resumable=True)
            uploaded_file = (
                service.files()
                .create(body=file_metadata, media_body=media, fields="id, name")
                .execute()
            )

            flash(
                f'Imagen "{uploaded_file.get('name')}" subida con éxito a Google Drive.',
                "success",
            )
            return redirect(url_for(".lab_dashboard"))

        except HttpError as error:
            flash(
                f"Ocurrió un error con la API de Google al subir el archivo: {error}",
                "danger",
            )
        except Exception as e:
            flash(f"Ocurrió un error inesperado al subir el archivo: {e}", "danger")

        return redirect(request.url)

    # --- Lógica GET para listar archivos de Google Drive ---
    try:
        # 1. Buscar el ID de la carpeta "Objetos3D"
        parent_folder_id = find_or_create_folder(service, "Objetos3D")
        if not parent_folder_id:
            flash(
                'No se encontró o creó la carpeta "Objetos3D" en tu Google Drive.',
                "warning",
            )
            return render_template("threed_lab.html", is_authenticated=True, files=[])

        # 2. Buscar el ID de la subcarpeta "Salida"
        output_folder_id = find_or_create_folder(service, "Salida", parent_folder_id)
        if not output_folder_id:
            flash(
                'No se encontró o creó la subcarpeta "Salida" dentro de "Objetos3D".',
                "warning",
            )
            return render_template("threed_lab.html", is_authenticated=True, files=[])

        # 3. Listar archivos .glb en la carpeta "Salida"
        response = (
            service.files()
            .list(
                q=f"'{output_folder_id}' in parents and name contains '.glb'",
                spaces="drive",
                fields="files(id, name, webContentLink, thumbnailLink)",
            )
            .execute()
        )
        drive_files = response.get("files", [])

        return render_template(
            "threed_lab.html", is_authenticated=True, files=drive_files
        )

    except HttpError as error:
        flash(f"Ocurrió un error con la API de Google: {error}", "danger")
        return render_template("threed_lab.html", is_authenticated=False)
    except Exception as e:
        flash(f"Ocurrió un error inesperado: {e}", "danger")
        return render_template("threed_lab.html", is_authenticated=False)


def background_image_to_3d_task(app, api_key, image_data, original_filename, mimetype):
    with app.app_context():
        try:
            headers = {"Authorization": f"Bearer {api_key}"}
            files = {"image": (original_filename, io.BytesIO(image_data), mimetype)}

            response = requests.post(
                "https://api.aimlapi.com/v1/image-to-3d",
                headers=headers,
                files=files,
                timeout=300,
            )
            response.raise_for_status()

            data = response.json()
            model_url = data.get("output_url")

            if not model_url:
                socketio.emit('model_generated', {'status': 'error', 'message': 'La API no devolvió una URL para el modelo.'})
                return

            model_response = requests.get(model_url, timeout=120)
            model_response.raise_for_status()

            models_dir = os.path.join(current_app.static_folder, "models")
            os.makedirs(models_dir, exist_ok=True)

            base_filename = os.path.splitext(original_filename)[0]
            new_filename = f"{base_filename}_{int(time.time())}.glb"
            model_path = os.path.join(models_dir, new_filename)

            with open(model_path, "wb") as f:
                f.write(model_response.content)

            socketio.emit('model_generated', {'status': 'success', 'filename': new_filename})

        except requests.exceptions.RequestException as e:
            socketio.emit('model_generated', {'status': 'error', 'message': f"Error al contactar la API: {e}"})
        except Exception as e:
            socketio.emit('model_generated', {'status': 'error', 'message': f"Ocurrió un error inesperado: {e}"})


@threed_lab_bp.route("/image-to-3d", methods=["GET", "POST"])
def image_to_3d():
    if request.method == "POST":
        api_key_setting = Setting.query.filter_by(key="AIMLAPI_KEY").first()
        if not api_key_setting or not api_key_setting.value:
            flash(
                "La clave de API para AIMLAPI no está configurada en Ajustes.", "danger"
            )
            return redirect(url_for(".image_to_3d"))

        if "image_file" not in request.files:
            flash("No se encontró el archivo de imagen.", "danger")
            return redirect(request.url)
        file = request.files["image_file"]
        if file.filename == "":
            flash("No se seleccionó ningún archivo.", "danger")
            return redirect(request.url)

        if file:
            image_data = file.read()
            thread = Thread(target=background_image_to_3d_task, args=(current_app._get_current_object(), api_key_setting.value, image_data, file.filename, file.mimetype))
            thread.start()
            flash("La conversión a 3D ha comenzado. Serás notificado cuando termine.", "info")
            return redirect(url_for(".lab_dashboard"))

    return render_template("image_to_3d.html", title="Crear Objeto 3D desde Imagen")


@threed_lab_bp.route("/delete_model/<string:file_id>", methods=["POST"])
def delete_model(file_id):
    service, auth_status = get_drive_service()

    if auth_status != "authenticated":
        flash("No estás autenticado con Google Drive.", "danger")
        return redirect(url_for(".lab_dashboard"))

    try:
        service.files().delete(fileId=file_id).execute()
        flash("Modelo eliminado de Google Drive con éxito.", "success")
    except HttpError as error:
        flash(f"Ocurrió un error al eliminar el archivo: {error}", "danger")
    except Exception as e:
        flash(f"Ocurrió un error inesperado: {e}", "danger")

    return redirect(url_for(".lab_dashboard"))


@threed_lab_bp.route("/rename_model/<string:file_id>", methods=["POST"])
def rename_model(file_id):
    service, auth_status = get_drive_service()

    if auth_status != "authenticated":
        flash("No estás autenticado con Google Drive.", "danger")
        return redirect(url_for(".lab_dashboard"))

    new_name = request.form.get("new_name")
    if not new_name:
        flash("No se proporcionó un nuevo nombre.", "danger")
        return redirect(url_for(".lab_dashboard"))

    try:
        file_metadata = {'name': new_name}
        service.files().update(fileId=file_id, body=file_metadata).execute()
        flash(f"Modelo renombrado a '{new_name}' con éxito.", "success")
    except HttpError as error:
        flash(f"Ocurrió un error al renombrar el archivo: {error}", "danger")
    except Exception as e:
        flash(f"Ocurrió un error inesperado: {e}", "danger")

    return redirect(url_for(".lab_dashboard"))


# Las rutas para eliminar, editar y ver se desactivan temporalmente
# ya que operaban sobre la base de datos local. Necesitarán ser re-implementadas
# para operar sobre Google Drive.

@threed_lab_bp.route("/interactive_spheres")
def interactive_spheres():
    """Muestra el laboratorio de esferas 3D interactivas."""
    return render_template("threed_lab/interactive_spheres.html", title="Laboratorio de Esferas 3D")
