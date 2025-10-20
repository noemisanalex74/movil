# agp-dashboard-web/blueprints/threed_lab.py
import json
import os
import shutil
import urllib.request

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
from werkzeug.utils import secure_filename

# Se importan condicionalmente para evitar errores en entornos sin la librería completa
try:
    from googleapiclient.discovery import build
    from googleapiclient.errors import HttpError
    from googleapiclient.http import MediaFileUpload
except ImportError:
    build = None
    HttpError = None
    MediaFileUpload = None

from models import Setting

threed_lab_bp = Blueprint("threed_lab", __name__, url_prefix="/lab-3d")

# --- Funciones de Ayuda (sin cambios) --- #

def get_drive_service():
    """Obtiene el objeto de servicio de Google Drive API o None si no está autenticado/configurado."""
    if not build:
        current_app.logger.error("La librería google-api-python-client no está instalada.")
        return None, "config_missing"

    client_id_setting = Setting.query.filter_by(key="GOOGLE_CLIENT_ID").first()
    client_secret_setting = Setting.query.filter_by(key="GOOGLE_CLIENT_SECRET").first()
    if not (client_id_setting and client_id_setting.value and client_secret_setting and client_secret_setting.value):
        return None, "config_missing"

    google_creds_setting = Setting.query.filter_by(key="GOOGLE_CREDENTIALS").first()
    if not google_creds_setting or not google_creds_setting.value:
        return None, "not_authenticated"

    try:
        creds_json = json.loads(google_creds_setting.value)
        creds = Credentials.from_authorized_user_info(creds_json)
        service = build("drive", "v3", credentials=creds)
        return service, "authenticated"
    except Exception as e:
        current_app.logger.error(f"Error al crear el servicio de Drive: {e}")
        return None, "not_authenticated"

def find_or_create_folder(service, folder_name, parent_id=None):
    """Busca una carpeta por nombre; si no existe, la crea."""
    q = f"mimeType='application/vnd.google-apps.folder' and name='{folder_name}' and trashed=false"
    if parent_id:
        q += f" and '{parent_id}' in parents"

    response = service.files().list(q=q, spaces="drive", fields="files(id, name)").execute()
    folders = response.get("files", [])

    if folders:
        return folders[0].get("id")
    else:
        file_metadata = {"name": folder_name, "mimeType": "application/vnd.google-apps.folder"}
        if parent_id:
            file_metadata["parents"] = [parent_id]
        folder = service.files().create(body=file_metadata, fields="id").execute()
        return folder.get("id")

def get_local_models_path():
    return os.path.join(current_app.static_folder, 'decenterland_models')

# --- NUEVAS RUTAS DE LAS 3 ESFERAS --- #

@threed_lab_bp.route("/lab")
def lab():
    """Esfera 1: El Laboratorio Principal / Visualizador."""
    # Por ahora, es una página simple. En el futuro, podría tener un visor 3D interactivo.
    return render_template("threed_lab/lab.html")

@threed_lab_bp.route("/gallery")
def gallery():
    """Esfera 2: Galería para ver los modelos 3D generados."""
    # Lógica para listar modelos locales
    local_models_path = get_local_models_path()
    local_models = []
    if os.path.exists(local_models_path):
        local_models = sorted([f for f in os.listdir(local_models_path) if f.endswith('.glb')])

    # Lógica para listar modelos de Google Drive
    service, auth_status = get_drive_service()
    drive_files = []
    if auth_status == "authenticated":
        folder_objetos3d_name = "AGP_Dashboard/3D_Lab"
        folder_salida_name = "Salida"
        try:
            parent_folder_id = find_or_create_folder(service, folder_objetos3d_name)
            output_folder_id = find_or_create_folder(service, folder_salida_name, parent_id=parent_folder_id)
            response = service.files().list(
                q=f"'{output_folder_id}' in parents and name contains '.glb' and trashed=false",
                spaces="drive", fields="files(id, name, webContentLink, thumbnailLink)",
                orderBy="modifiedTime desc"
            ).execute()
            drive_files = response.get("files", [])
        except HttpError as error:
            flash(f"Ocurrió un error con la API de Google al listar modelos: {error}", "danger")
        except Exception as e:
            flash(f"Ocurrió un error inesperado con Google Drive: {e}", "danger")

    return render_template("threed_lab/gallery.html",
                           is_authenticated=(auth_status == "authenticated"),
                           config_missing=(auth_status == "config_missing"),
                           drive_files=drive_files,
                           local_models=local_models)

@threed_lab_bp.route("/upload", methods=["GET", "POST"])
def upload():
    """Esfera 3: Carga de material (imágenes) para procesar."""
    service, auth_status = get_drive_service()

    if auth_status != "authenticated":
        # Si no está autenticado, no se puede subir. Muestra la info en la plantilla.
        return render_template("threed_lab/upload.html",
                               is_authenticated=False,
                               config_missing=(auth_status == "config_missing"))

    if request.method == "POST":
        if 'image_files' not in request.files:
            flash("No se encontraron archivos en la solicitud.", "warning")
            return redirect(url_for(".upload"))

        files = request.files.getlist("image_files")
        if not files or all(f.filename == '' for f in files):
            flash("No se seleccionó ningún archivo de imagen.", "warning")
            return redirect(url_for(".upload"))

        try:
            folder_objetos3d_name = "AGP_Dashboard/3D_Lab"
            folder_entrada_name = "Entrada"
            parent_folder_id = find_or_create_folder(service, folder_objetos3d_name)
            input_folder_id = find_or_create_folder(service, folder_entrada_name, parent_id=parent_folder_id)
            
            uploaded_count = 0
            for file in files:
                if file and file.filename != '':
                    model_name = secure_filename(file.filename)
                    # Usar file.stream en lugar de guardar en disco
                    media = MediaFileUpload(file.stream, mimetype=file.mimetype, resumable=True)
                    service.files().create(body={"name": model_name, "parents": [input_folder_id]}, media_body=media).execute()
                    uploaded_count += 1
            
            if uploaded_count > 0:
                flash(f"Se subieron {uploaded_count} imágenes a la carpeta 'Entrada' de Google Drive.", "success")
            
            return redirect(url_for(".gallery")) # Redirigir a la galería para ver el resultado eventualmente

        except HttpError as error:
            flash(f"Ocurrió un error con la API de Google al subir archivos: {error}", "danger")
        except Exception as e:
            flash(f"Ocurrió un error inesperado al subir archivos: {e}", "danger")
        
        return redirect(url_for(".upload"))

    # Para peticiones GET
    return render_template("threed_lab/upload.html", is_authenticated=True, config_missing=False)


# --- Rutas de Acciones (actualizadas para redirigir a la galería) --- #

@threed_lab_bp.route("/local/generate", methods=['POST'])
def local_generate():
    models_path = get_local_models_path()
    os.makedirs(models_path, exist_ok=True)
    try:
        # Simulación de creación de modelos
        url = 'https://raw.githubusercontent.com/KhronosGroup/glTF-Sample-Models/master/2.0/Duck/glTF-Binary/Duck.glb'
        base_model_name = 'drone_biplaza.glb'
        base_model_path = os.path.join(models_path, base_model_name)
        
        if not os.path.exists(base_model_path):
            urllib.request.urlretrieve(url, base_model_path)
        
        wearables = ['helmet_agp.glb', 'jetpack_agp.glb', 'glasses_agp.glb']
        for w_name in wearables:
            shutil.copy(base_model_path, os.path.join(models_path, w_name))
        
        flash('Modelos locales de ejemplo generados/actualizados.', 'success')
    except Exception as e:
        flash(f'Error al generar los modelos locales: {e}', 'danger')
    return redirect(url_for('.gallery'))

@threed_lab_bp.route("/local/delete", methods=['POST'])
def local_delete():
    models_path = get_local_models_path()
    try:
        if os.path.exists(models_path):
            shutil.rmtree(models_path)
            flash('Todos los modelos locales han sido eliminados.', 'success')
        else:
            flash('La carpeta de modelos locales no existe.', 'info')
    except Exception as e:
        flash(f'Error al eliminar los modelos locales: {e}', 'danger')
    return redirect(url_for('.gallery'))

@threed_lab_bp.route("/delete/<string:file_id>", methods=["POST"])
def delete_model(file_id):
    service, auth_status = get_drive_service()
    if auth_status != "authenticated":
        flash("No estás autenticado con Google Drive.", "danger")
        return redirect(url_for(".gallery"))

    try:
        service.files().delete(fileId=file_id).execute()
        flash("Modelo eliminado de Google Drive con éxito.", "success")
    except HttpError as error:
        flash(f"Ocurrió un error al eliminar el archivo: {error}", "danger")
    
    return redirect(url_for(".gallery"))
