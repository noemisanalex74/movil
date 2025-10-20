import json
import os

# Rutas a los archivos de datos del CLI principal
CONFIG_FILE = "/data/data/com.termux/files/home/agp-gemini-cli/config.json"
TAREAS_FILE = "/data/data/com.termux/files/home/agp-gemini-cli/tareas.json"
CONTEXT_MEMORY_FILE = (
    "/data/data/com.termux/files/home/agp-gemini-cli/context_memory.json"
)
CUSTOM_TOOLS_DIR = "/data/data/com.termux/files/home/agp-gemini-cli/custom_tools"
ENV_DIR = os.path.join(os.path.expanduser("~"), ".virtualenvs")


def get_config_data():
    try:
        with open(CONFIG_FILE, "r") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return {}


def get_tasks_data():
    try:
        with open(TAREAS_FILE, "r") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return []


def get_context_memory_data():
    try:
        with open(CONTEXT_MEMORY_FILE, "r") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return {}


def get_custom_tools_data():
    tools = []
    if os.path.exists(CUSTOM_TOOLS_DIR) and os.listdir(CUSTOM_TOOLS_DIR):
        for filename in os.listdir(CUSTOM_TOOLS_DIR):
            if filename.endswith(".py") and filename != "__init__.py":
                tools.append(filename)
    return tools


def get_virtual_envs_data():
    envs = []
    if os.path.exists(ENV_DIR) and os.listdir(ENV_DIR):
        for item in os.listdir(ENV_DIR):
            item_path = os.path.join(ENV_DIR, item)
            if os.path.isdir(item_path) and os.path.exists(
                os.path.join(item_path, "bin", "activate")
            ):
                envs.append(f"{item} ({item_path})")
    return envs
