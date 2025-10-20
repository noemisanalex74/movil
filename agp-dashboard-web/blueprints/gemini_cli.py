import os
import sys

from flask import Blueprint, jsonify, render_template, request, session

# Adjust path to import from agp-gemini-cli
# This ensures we can import the chat_with_gemini function
sys.path.append(
    os.path.abspath(
        os.path.join(os.path.dirname(__file__), "..", "..", "agp-gemini-cli")
    )
)

# Conditionally import gemini_interface or define dummy functions for testing
if not os.environ.get("FLASK_TESTING"):
    from gemini_interface import chat_with_gemini, generar_idea
else:
    # Dummy functions for when google.generativeai is not installed or in testing mode
    def chat_with_gemini(*args, **kwargs):
        print("Mock chat_with_gemini called (FLASK_TESTING is True)")
        return [], "Mock response (FLASK_TESTING is True)"

    def generar_idea(*args, **kwargs):
        print("Mock generar_idea called (FLASK_TESTING is True)")
        return "Mock idea (FLASK_TESTING is True)"

from models import Setting

gemini_cli_bp = Blueprint("gemini_cli", __name__)


@gemini_cli_bp.route("/gemini_cli")
def gemini_cli_page():
    """
    Renders the main page for the Gemini CLI interface.
    Clears the chat history for a new session.
    """
    session.pop("gemini_chat_history", None)
    return render_template("gemini_cli.html")


@gemini_cli_bp.route("/gemini_cli/send_message", methods=["POST"])
def send_message():
    """
    Handles the AJAX request to send a message to the Gemini model,
    maintaining conversation history.
    """
    user_message = request.json.get("message")
    if not user_message:
        return jsonify({"error": "No message provided"}), 400

    # Load history from session or start a new one
    chat_history = session.get("gemini_chat_history", [])

    try:
        # Get API Key from database
        api_key_setting = Setting.query.filter_by(key="GEMINI_API_KEY").first()
        api_key = api_key_setting.value if api_key_setting else None

        if not api_key:
            return (
                jsonify(
                    {
                        "error": "La clave de API de Gemini no está configurada en la página de Ajustes."
                    }
                ),
                500,
            )

        # If the history is empty, it's the first message.
        if not chat_history:
            model_response = generar_idea(user_message, api_key=api_key)
            updated_history = [
                {"role": "user", "parts": [{"text": user_message}]},
                {"role": "model", "parts": [{"text": model_response}]},
            ]
        else:
            updated_history, model_response = chat_with_gemini(
                chat_history, user_message, api_key=api_key
            )

        # Save the updated history back to the session
        session["gemini_chat_history"] = updated_history

        return jsonify({"response": model_response})
    except Exception as e:
        # Log the error for debugging
        print(f"Error communicating with Gemini: {e}")
        # Return a user-friendly error message
        error_message = f"Error al comunicarse con la API de Gemini: {e}"
        return jsonify({"error": error_message}), 500


@gemini_cli_bp.route("/gemini_cli/execute_command", methods=["POST"])
def execute_command():
    """
    Executes a shell command received from the frontend.
    """
    command = request.json.get("command")
    if not command:
        return jsonify({"error": "No command provided"}), 400

    try:
        # Execute the command.
        # NOTE: Using shell=True can be a security risk if the command is not
        # properly sanitized. Here we trust the commands suggested by the model.
        # For a production environment, a whitelist of allowed commands would be safer.
        import subprocess

        result = subprocess.run(
            command,
            shell=True,
            capture_output=True,
            text=True,
            check=True,  # This will raise a CalledProcessError for non-zero exit codes
            cwd=os.path.abspath(
                os.path.join(os.path.dirname(__file__), "..", "..")
            ),  # Run in project root
        )
        output = result.stdout
        return jsonify({"output": output})
    except subprocess.CalledProcessError as e:
        # This catches errors from the command itself (e.g., command not found, script error)
        error_output = f"""Error al ejecutar el comando.
--- STDOUT ---
{e.stdout}
--- STDERR ---
{e.stderr}"""
        return jsonify({"error": error_output}), 500
    except Exception as e:
        # This catches other errors (e.g., issues with subprocess itself)
        return jsonify({"error": f"An unexpected error occurred: {e}"}), 500
