
import os
import shutil
import subprocess
import uuid
from datetime import datetime

from flask import Blueprint, current_app, jsonify, render_template, request
from utils import _load_json, _save_json

visual_notes_bp = Blueprint("visual_notes", __name__)

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
NOTES_FILE = os.path.join(BASE_DIR, "instance", "visual_notes.json")
UPLOADS_DIR = os.path.join(BASE_DIR, "instance", "uploads")

@visual_notes_bp.route("/visual_notes")
def show_notes():
    """Renders the gallery of visual notes."""
    notes = _load_json(NOTES_FILE, [])
    return render_template("visual_notes.html", notes=notes)

@visual_notes_bp.route("/api/visual_notes/create", methods=["POST"])
def create_note():
    """Creates a new visual note by taking a photo."""
    description = request.form.get("description", "Sin descripción")
    
    # Ensure upload directory exists
    os.makedirs(UPLOADS_DIR, exist_ok=True)
    
    temp_photo_path = os.path.join(UPLOADS_DIR, f"temp_{uuid.uuid4()}.jpg")
    final_filename = f"note_{uuid.uuid4()}.jpg"
    final_photo_path = os.path.join(UPLOADS_DIR, final_filename)

    try:
        # Take a photo using Termux:API
        subprocess.run(
            ['termux-camera-photo', '-c', '0', temp_photo_path],
            check=True, timeout=60
        )

        if not os.path.exists(temp_photo_path):
            return jsonify({"error": "No se pudo capturar la imagen."}), 500

        # Rename the file to its final name
        shutil.move(temp_photo_path, final_photo_path)

        # Create metadata for the note
        new_note = {
            "id": str(uuid.uuid4()),
            "description": description,
            "filename": final_filename,
            "timestamp": datetime.now().isoformat()
        }

        notes = _load_json(NOTES_FILE, [])
        notes.insert(0, new_note) # Add to the beginning
        _save_json(NOTES_FILE, notes)

        return jsonify(new_note), 201

    except subprocess.TimeoutExpired:
        return jsonify({"error": "El comando de la cámara tardó demasiado en responder."}), 500
    except subprocess.CalledProcessError as e:
        return jsonify({"error": f"Error al usar la cámara: {e}"}), 500
    except Exception as e:
        current_app.logger.error(f"Error creating visual note: {e}")
        return jsonify({"error": "Ocurrió un error inesperado."}), 500
