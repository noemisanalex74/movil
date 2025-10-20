import json
import os


def load_json_file(file_path: str, default_value=None):
    """Carga un archivo JSON. Retorna el contenido o un valor por defecto si hay un error."""
    try:
        with open(file_path, "r") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return default_value


def save_json_file(file_path: str, data):
    """Guarda datos en un archivo JSON."""
    with open(file_path, "w") as f:
        json.dump(data, f, indent=2)


def load_project_state(
    project_path: str, file_name: str = ".agp_project_state.json"
) -> dict:
    """Carga el estado de un proyecto desde su archivo JSON."""
    state_file_path = os.path.join(project_path, file_name)
    return load_json_file(state_file_path, {})


def save_project_state(
    project_path: str, state: dict, file_name: str = ".agp_project_state.json"
):
    """Guarda el estado de un proyecto en su archivo JSON."""
    state_file_path = os.path.join(project_path, file_name)
    save_json_file(state_file_path, state)
