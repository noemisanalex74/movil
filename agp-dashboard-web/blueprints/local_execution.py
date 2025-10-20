import json
import os
import subprocess

from flask import Blueprint, current_app, jsonify, render_template, request
from gtts import gTTS

local_execution_bp = Blueprint("local_execution", __name__)

COMMANDS_FILE = os.path.join(
    os.path.dirname(__file__), "..", "instance", "allowed_local_commands.json"
)


def _load_allowed_commands():
    """Loads the allowed local commands from the JSON file."""
    try:
        with open(COMMANDS_FILE, "r") as f:
            data = json.load(f)
            return data.get("commands", [])
    except (FileNotFoundError, json.JSONDecodeError):
        return []


@local_execution_bp.route("/local_execution")
def execution_page():
    """Renders the local command execution page."""
    commands = _load_allowed_commands()
    return render_template("local_execution.html", commands=commands)


@local_execution_bp.route("/local_execution/run", methods=["POST"])
def run_command():
    """Runs a whitelisted local command."""
    command_name = request.json.get("name")
    if not command_name:
        return jsonify({"error": "No command name provided"}), 400

    allowed_commands = _load_allowed_commands()
    command_to_run = next(
        (cmd for cmd in allowed_commands if cmd["name"] == command_name), None
    )

    if not command_to_run:
        return jsonify({"error": "Command not allowed"}), 403

    try:
        # Execute the command. Using the full command from the JSON file.
        result = subprocess.run(
            command_to_run["command"],
            shell=True,
            capture_output=True,
            text=True,
            check=True,
            cwd=current_app.root_path,  # Run in the dashboard's root directory
        )
        return jsonify({"output": result.stdout})
    except subprocess.CalledProcessError as e:
        error_output = f"Error executing command.\n--- STDOUT ---\n{e.stdout}\n--- STDERR ---\n{e.stderr}"
        return jsonify({"error": error_output}), 500
    except Exception as e:
        return jsonify({"error": f"An unexpected error occurred: {e}"}), 500


@local_execution_bp.route('/speech-to-text', methods=['POST'])
def speech_to_text():
    """Uses termux-speech-to-text to capture voice and return it as text."""
    try:
        # Run the Termux API command
        result = subprocess.run(
            ['termux-speech-to-text'],
            capture_output=True,
            text=True,
            check=True,
            timeout=20  # 20 seconds to speak
        )
        # The result is plain text, so we wrap it in JSON
        text_output = result.stdout.strip()
        return jsonify({'text': text_output, 'error': None})
    except subprocess.CalledProcessError as e:
        # This can happen if the user cancels the voice input
        current_app.logger.warn("Speech-to-text cancelled or failed", error=e.stderr)
        return jsonify({'text': '', 'error': 'Speech recognition was cancelled or failed.'}), 400
    except FileNotFoundError:
        return jsonify({'text': '', 'error': 'Termux:API is not installed or `termux-speech-to-text` not found.'}), 500
    except Exception as e:
        current_app.logger.error("Unexpected error in speech-to-text", error=str(e))
        return jsonify({'text': '', 'error': f'An unexpected error occurred: {e}'}), 500

@local_execution_bp.route('/text-to-speech', methods=['POST'])
def text_to_speech():
    # Temporary comment to force Flask to re-evaluate this blueprint
    """Converts text to speech and plays it."""
    text = request.json.get("text")
    if not text:
        return jsonify({"error": "No text provided"}), 400

    try:
        # Create gTTS object
        tts = gTTS(text=text, lang='es')
        
        # Save to a temporary file
        speech_file = "/data/data/com.termux/files/usr/tmp/speech.mp3"
        tts.save(speech_file)
        
        # Play the audio file
        subprocess.run(['mpg123', speech_file], check=True)
        
        # Clean up the file
        os.remove(speech_file)
        
        return jsonify({"status": "success"})
        
    except FileNotFoundError:
        return jsonify({'error': '`mpg123` is not installed. Please run `pkg install mpg123`.'}), 500
    except Exception as e:
        current_app.logger.error(f"Error in text-to-speech: {e}")
        return jsonify({"error": str(e)}), 500
