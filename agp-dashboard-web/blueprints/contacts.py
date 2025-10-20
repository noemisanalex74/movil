
import json
import subprocess

from flask import Blueprint, current_app, jsonify, render_template, request

contacts_bp = Blueprint("contacts", __name__)

@contacts_bp.route("/contacts")
def show_contacts():
    """Fetches contacts from Termux:API and renders them."""
    try:
        result = subprocess.run(
            ['termux-contact-list'],
            capture_output=True, text=True, check=True, timeout=15
        )
        contacts = json.loads(result.stdout)
    except Exception as e:
        current_app.logger.error(f"Could not fetch contacts: {e}")
        contacts = []
        # You could flash a message to the user here
    
    return render_template("contacts.html", contacts=contacts)

@contacts_bp.route("/api/contacts/call", methods=["POST"])
def make_call():
    """Initiates a phone call using Termux:API."""
    data = request.get_json()
    number = data.get("number")

    if not number:
        return jsonify({"error": "Número de teléfono no proporcionado."}), 400

    try:
        subprocess.run(
            ['termux-telephony-call', number],
            check=True, timeout=10
        )
        return jsonify({"message": f"Llamando al número {number}..."})
    except Exception as e:
        current_app.logger.error(f"Failed to make call: {e}")
        return jsonify({"error": "No se pudo iniciar la llamada."}), 500
