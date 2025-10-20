
from flask import Blueprint, jsonify, request

assistant_bp = Blueprint("assistant", __name__)

@assistant_bp.route("/api/assistant/command", methods=["POST"])
def process_command():
    data = request.get_json()
    text = data.get("text", "").lower()

    if not text:
        return jsonify({"response_text": "No entendí lo que dijiste."})

    # Simple keyword-based intent parsing (to be expanded)
    if "hola" in text:
        response_text = "Hola, Alejandro. ¿En qué puedo ayudarte?"
    elif "cuántas tareas" in text:
        # Placeholder - logic to be implemented
        response_text = "Actualmente tienes 5 tareas pendientes. Esta es una respuesta de prueba."
    else:
        response_text = f"Recibí tu comando: {text}. Pero todavía no sé cómo procesarlo."

    return jsonify({"response_text": response_text})
