import json
import logging
import os
import subprocess
import sys
from datetime import datetime

import structlog
import typer
from commands.git_commands import git_app
from commands.github_commands import github_app
from commands.mcp_commands import mcp_app
from commands.tools import tools_app
from dotenv import dotenv_values, load_dotenv
from escuchar import escuchar_y_responder
from file_utils import (
    load_json_file,
    save_json_file,
)
from gemini_interface import chat_with_gemini, generar_idea
from utils import (
    crear_archivo_proyecto,
    eliminar_archivo_proyecto,
    escribir_archivo_proyecto,
    leer_archivo_proyecto,
    listen_and_recognize,
    notificar,
    speak,
)

# Cargar variables de entorno del archivo .env
load_dotenv()

# --- Structured Logging Configuration ---
logging.basicConfig(level=logging.INFO, format="%(message)s", stream=sys.stdout)
log = structlog.get_logger()
# --- End of Logging Configuration ---

# --- Variables y Funciones de Utilidad Globales ---
ALIASES_FILE = "aliases.json"
TAREAS_FILE = "tareas.json"
CHAT_HISTORY_FILE = "chat_history.json"
NOTAS_FILE = "/data/data/com.termux/files/home/agp-gemini-cli/notas.txt"
# Directorio centralizado para entornos virtuales
ENV_DIR = os.path.join(os.path.expanduser("~"), ".virtualenvs")

def _cargar_env():
    """Carga los datos del archivo .env de la raíz del proyecto como un diccionario."""
    project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    env_path = os.path.join(project_root, ".env")
    return dotenv_values(env_path)

def _guardar_env(env_data):
    """Guarda un diccionario de datos en el archivo .env de la raíz del proyecto."""
    project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    env_path = os.path.join(project_root, ".env")
    with open(env_path, "w") as f:
        for key, value in env_data.items():
            f.write(f'{key}="{value}"\n')

def _cargar_aliases():
    return load_json_file(ALIASES_FILE, {})

def _guardar_aliases(aliases_data):
    save_json_file(ALIASES_FILE, aliases_data)

def _cargar_tareas():
    return load_json_file(TAREAS_FILE, [])

def _guardar_tareas(tareas):
    save_json_file(TAREAS_FILE, tareas)

# --- Gestión de Entornos Virtuales ---
env_app = typer.Typer(name="env", help="Gestiona entornos virtuales de Python.")

@env_app.command(name="create")
def env_create(name: str = typer.Argument(..., help="Nombre del entorno virtual a crear.")):
    """Crea un nuevo entorno virtual de Python."""
    env_path = os.path.join(ENV_DIR, name)
    if os.path.exists(env_path):
        typer.secho(f"Error: El entorno virtual '{name}' ya existe en {env_path}.",
                    fg=typer.colors.RED)
        raise typer.Abort()

    typer.secho(f"Creando entorno virtual '{name}' en {env_path}...",
                fg=typer.colors.WHITE)
    try:
        subprocess.run([sys.executable, "-m", "venv", env_path], check=True)
        typer.secho(f"✅ Entorno virtual '{name}' creado con éxito.",
                    fg=typer.colors.GREEN)
        typer.echo(f"Para activarlo, usa: source {env_path}/bin/activate")
    except subprocess.CalledProcessError as e:
        typer.secho(f"Error al crear el entorno virtual: {e.stderr}",
                    fg=typer.colors.RED)
    except Exception as e:
        typer.secho(f"Ha ocurrido un error inesperado: {e}", fg=typer.colors.RED)

@env_app.command(name="activate")
def env_activate(name: str = typer.Argument(..., help="Nombre del entorno virtual a activar.")):
    """Muestra las instrucciones para activar un entorno virtual."""
    env_path = os.path.join(ENV_DIR, name)
    if not os.path.exists(env_path):
        typer.secho(f"Error: El entorno virtual '{name}' no existe en {env_path}.",
                    fg=typer.colors.RED)
        raise typer.Abort()

    typer.secho(f"Para activar el entorno virtual '{name}', ejecuta:",
                fg=typer.colors.WHITE)
    typer.secho(f"source {env_path}/bin/activate", fg=typer.colors.CYAN)
    typer.secho("Recuerda que esto debe hacerse en tu shell, no dentro del CLI.",
                fg=typer.colors.YELLOW)

@env_app.command(name="list")
def env_list():
    """Lista todos los entornos virtuales creados por AGP CLI."""
    typer.secho("--- ENTORNOS VIRTUALES ---", fg=typer.colors.BRIGHT_MAGENTA)
    if not os.path.exists(ENV_DIR) or not os.listdir(ENV_DIR):
        typer.secho("No hay entornos virtuales creados.", fg=typer.colors.YELLOW)
        return

    found_envs = False
    for item in os.listdir(ENV_DIR):
        item_path = os.path.join(ENV_DIR, item)
        if (os.path.isdir(item_path) and
            os.path.exists(os.path.join(item_path, "bin", "activate"))):
            typer.echo(f"- {item} ({item_path})")
            found_envs = True

    if not found_envs:
        typer.echo("No hay entornos virtuales creados.")

    typer.secho("--------------------------", fg=typer.colors.BRIGHT_MAGENTA)

@env_app.command(name="remove")
def env_remove(name: str = typer.Argument(..., help="Nombre del entorno virtual a eliminar.")):
    """Elimina un entorno virtual."""
    env_path = os.path.join(ENV_DIR, name)
    if not os.path.exists(env_path):
        typer.secho(f"Error: El entorno virtual '{name}' no existe en {env_path}.",
                    fg=typer.colors.RED)
        raise typer.Abort()

    if typer.confirm(f"¿Estás seguro de que quieres eliminar el entorno virtual '{name}'? "
                     f"Esta acción es irreversible."):
        try:
            import shutil
            shutil.rmtree(env_path)
            typer.secho(f"✅ Entorno virtual '{name}' eliminado con éxito.",
                        fg=typer.colors.GREEN)
        except Exception as e:
            typer.secho(f"Error al eliminar el entorno virtual: {e}",
                        fg=typer.colors.RED)
    else:
        typer.secho("Operación cancelada.", fg=typer.colors.YELLOW)

# --- App Principal de Typer ---
app = typer.Typer()

app.add_typer(git_app, name="git")
app.add_typer(github_app, name="github")
app.add_typer(env_app, name="env")
app.add_typer(tools_app, name="tools")
app.add_typer(mcp_app, name="mcp")

# --- Comandos Principales ---

@app.command()
def dashboard():
    """Muestra un resumen del estado actual del proyecto y la configuración de AGP CLI."""
    log.info("📊 Dashboard del Proyecto AGP CLI 📊")
    typer.echo("")

    # --- Información General ---
    typer.secho("--- Información General ---", fg=typer.colors.BRIGHT_MAGENTA)
    typer.secho(f"Directorio de Trabajo: {os.getcwd()}", fg=typer.colors.WHITE)
    typer.secho(f"Sistema Operativo: {sys.platform}", fg=typer.colors.WHITE)
    typer.echo("")

    # --- Estado de la IA y Configuración ---
    typer.secho("--- Estado de la IA y Configuración ---",
                fg=typer.colors.BRIGHT_MAGENTA)
    gemini_api_key_status = ("Configurada ✅" if os.environ.get("GEMINI_API_KEY")
                             else "No configurada ❌")
    github_token_status = ("Configurado ✅" if os.environ.get("GITHUB_TOKEN")
                           else "No configurado ❌")
    typer.secho(f"API Key de Gemini: {gemini_api_key_status}", fg=typer.colors.WHITE)
    typer.secho(f"Token de GitHub: {github_token_status}", fg=typer.colors.WHITE)
    typer.echo("")

    # --- Preferencias del Usuario (desde context_memory.json) ---
    typer.secho("--- Preferencias del Usuario ---", fg=typer.colors.BRIGHT_MAGENTA)
    try:
        with open("/data/data/com.termux/files/home/agp-gemini-cli/context_memory.json",
                  "r") as f:
            context_memory = json.load(f)
        preferencias = context_memory.get("preferencias", {})
        if preferencias:
            for key, value in preferencias.items():
                typer.secho(f"- {key.replace('_', ' ').title()}: {value}",
                            fg=typer.colors.WHITE)
        else:
            typer.secho("No hay preferencias de usuario guardadas.",
                        fg=typer.colors.YELLOW)
    except (FileNotFoundError, json.JSONDecodeError):
        typer.secho("No se pudo cargar context_memory.json o está vacío.",
                    fg=typer.colors.YELLOW)
    typer.echo("")

    # --- Tareas Pendientes ---
    typer.secho("--- Tareas Pendientes ---", fg=typer.colors.BRIGHT_MAGENTA)
    tareas = _cargar_tareas()
    pendientes = [t for t in tareas if t.get("estado") == "pendiente"]
    if pendientes:
        for i, tarea in enumerate(pendientes):
            typer.secho(f"- {i+1}. {tarea['descripcion']}", fg=typer.colors.WHITE)
    else:
        typer.secho("No hay tareas pendientes. ¡Bien hecho! ✅",
                    fg=typer.colors.GREEN)
    typer.echo("")

    # --- Herramientas Personalizadas (MCP) ---
    typer.secho("--- Herramientas Personalizadas (MCP) ---",
                fg=typer.colors.BRIGHT_MAGENTA)
    custom_tools_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                    "custom_tools")
    if os.path.exists(custom_tools_dir) and os.listdir(custom_tools_dir):
        for filename in os.listdir(custom_tools_dir):
            if filename.endswith(".py") and filename != "__init__.py":
                typer.secho(f"- {filename}", fg=typer.colors.WHITE)
    else:
        typer.secho("No hay herramientas personalizadas instaladas.",
                    fg=typer.colors.YELLOW)
    typer.echo("")

    # --- Entornos Virtuales ---
    typer.secho("--- Entornos Virtuales ---", fg=typer.colors.BRIGHT_MAGENTA)
    if os.path.exists(ENV_DIR) and os.listdir(ENV_DIR):
        found_envs = False
        for item in os.listdir(ENV_DIR):
            item_path = os.path.join(ENV_DIR, item)
            if (os.path.isdir(item_path) and
                os.path.exists(os.path.join(item_path, "bin", "activate"))):
                typer.secho(f"- {item} ({item_path})", fg=typer.colors.WHITE)
                found_envs = True
        if not found_envs:
            typer.secho("No hay entornos virtuales creados por AGP CLI.",
                        fg=typer.colors.YELLOW)
    else:
        typer.secho("No hay entornos virtuales creados por AGP CLI.",
                    fg=typer.colors.YELLOW)
    typer.echo("")

@app.command()
def hablar(prompt: str):
    """Envia un prompt a la IA de Gemini y muestra la respuesta."""
    respuesta = generar_idea(prompt)
    typer.secho(respuesta, fg=typer.colors.CYAN)
    speak(respuesta)
    notificar("AGP CLI", "Idea generada con éxito.")

@app.command()
def escuchar():
    """Activa el micrófono para que dictes tu idea a Gemini."""
    escuchar_y_responder()
    notificar("AGP CLI", "Idea generada por voz con éxito.")

@app.command()
def procesar_clipboard(instruccion: str):
    """Procesa el texto del portapapeles con una instrucción."""
    try:
        texto_portapapeles = subprocess.check_output(["termux-clipboard-get"],
                                                    text=True, check=True)
        prompt = f"{instruccion}:\n\n{texto_portapapeles}"
        respuesta = generar_idea(prompt)
        typer.echo(respuesta)
        speak(respuesta)
        notificar("AGP CLI", "Texto del portapapeles procesado.")
    except FileNotFoundError:
        typer.secho("Error: El comando 'termux-clipboard-get' no se encontró. "
                    "Asegúrate de que Termux:API está instalado y los permisos son correctos.",
                    fg=typer.colors.RED)
    except subprocess.CalledProcessError as e:
        typer.secho(f"Error al obtener el texto del portapapeles: {e.stderr}",
                    fg=typer.colors.RED)
    except Exception as e:
        typer.secho("Ha ocurrido un error inesperado al procesar el portapapeles: "
                    f"{e}", fg=typer.colors.RED)

@app.command()
def nota_rapida(nota: str):
    """Guarda una nota rápida con geolocalización."""
    try:
        location_data = subprocess.check_output(["termux-location"], text=True,
                                                check=True)
        location = json.loads(location_data)
        lat = location.get('latitude')
        lon = location.get('longitude')
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        nota_formateada = (
            f"--- NOTA ---\n"
            f"Fecha: {timestamp}\n"
            f"Ubicación: Lat {lat}, Lon {lon}\n"
            f"Nota: {nota}\n"
            f"------------------\n\n"
        )
        with open(NOTAS_FILE, "a") as f:
            f.write(nota_formateada)
        typer.secho("✅ Nota guardada con éxito en notas.txt", fg=typer.colors.GREEN)
        notificar("AGP CLI", f"Nota rápida guardada: '{nota[:20]}...' ")
    except FileNotFoundError:
        typer.secho("Error: El comando 'termux-location' no encontrado. "
                    "Asegúrate de que Termux:API está instalado y con permisos de ubicación.",
                    fg=typer.colors.RED)
    except subprocess.CalledProcessError as e:
        typer.secho(f"Error al obtener la ubicación: {e.stderr}. "
                    "Asegúrate de tener el GPS activado y los permisos concedidos.",
                    fg=typer.colors.RED)
    except json.JSONDecodeError:
        typer.secho("Error al procesar los datos de ubicación. "
                    "Asegúrate de que el GPS está activo y Termux:API tiene permisos.",
                    fg=typer.colors.RED)
    except Exception as e:
        typer.secho(f"Ha ocurrido un error inesperado al guardar la nota: {e}",
                    fg=typer.colors.RED)

@app.command(name="listar-notas")
def listar_notas():
    """Muestra todas las notas guardadas."""
    try:
        with open(NOTAS_FILE, "r") as f:
            content = f.read()
            if not content.strip():
                typer.echo("No hay notas guardadas todavía.")
                return
            typer.echo("--- TODAS LAS NOTAS ---")
            typer.echo(content)
            typer.echo("-----------------------")
    except FileNotFoundError:
        typer.echo("No hay notas guardadas todavía.")

@app.command(name="buscar-nota")
def buscar_nota(termino: str):
    """Busca un término en todas las notas guardadas."""
    try:
        with open(NOTAS_FILE, "r") as f:
            content = f.read()
        notas = content.split("--- NOTA ---")[1:]
        encontradas = []
        for nota_cuerpo in notas:
            if nota_cuerpo.strip() and termino.lower() in nota_cuerpo.lower():
                encontradas.append("--- NOTA ---" + nota_cuerpo)
        if not encontradas:
            typer.echo(f"No se encontraron notas que contengan '{termino}'.")
            return
        typer.echo(f"--- NOTAS ENCONTRADAS PARA '{termino}' ---")
        for nota_completa in encontradas:
            typer.echo(nota_completa)
        typer.echo("------------------------------------")
    except FileNotFoundError:
        typer.echo("No hay notas guardadas todavía.")

def _buscar_numero_por_nombre(nombre: str) -> str | None:
    """Busca un número de teléfono en los contactos de Termux por nombre."""
    try:
        contact_list_json = subprocess.check_output(["termux-contact-list"], text=True)
        contact_list = json.loads(contact_list_json)
        contactos_encontrados = [c for c in contact_list if nombre.lower() in c.get('name', '').lower()]
        if not contactos_encontrados:
            typer.echo(f"No se encontró ningún contacto que coincida con '{nombre}'.")
            return None
        if len(contactos_encontrados) == 1:
            return contactos_encontrados[0].get('number')
        typer.echo(f"Se encontraron varios contactos para '{nombre}'. Por favor, elige uno:")
        for i, c in enumerate(contactos_encontrados):
            typer.echo(f"[{i+1}] {c.get('name')} ({c.get('number')})")
        seleccion = typer.prompt("Introduce el número de tu elección:", type=int)
        if 1 <= seleccion <= len(contactos_encontrados):
            return contactos_encontrados[seleccion - 1].get('number')
        else:
            typer.echo("Selección no válida.")
            return None
    except FileNotFoundError:
        typer.echo("Error: 'termux-contact-list' no encontrado. "
                   "Asegúrate de que Termux:API está instalado.")
        return None
    except json.JSONDecodeError:
        typer.echo("Error al procesar la lista de contactos. "
                   "Asegúrate de que los permisos son correctos.")
        return None
    except Exception as e:
        typer.echo(f"Ha ocurrido un error inesperado al buscar contactos: {e}")
        return None

@app.command()
def buscar_contacto(nombre: str):
    """Busca un contacto por nombre y muestra su número."""
    numero = _buscar_numero_por_nombre(nombre)
    if numero:
        typer.echo(f"El número de {nombre} es: {numero}")

@app.command()
def crear_sms(idea: str, para: str = typer.Option(None,
                                                  help="Nombre o número del destinatario.")):
    """Genera un borrador de SMS con IA y lo envía con tu aprobación."""
    numero_destinatario = para
    if para and not para.replace('+', '').isdigit():
        numero_destinatario = _buscar_numero_por_nombre(para)
        if not numero_destinatario:
            raise typer.Abort()
    elif not para:
        typer.secho("Debes proporcionar un nombre o un número de teléfono.",
                    fg=typer.colors.RED)
        raise typer.Abort()
    prompt = (f"Redacta un SMS profesional y conciso para enviar a {para} sobre la "
              f"siguiente idea: '{idea}'. El mensaje debe ser únicamente el texto a "
              f"enviar, sin saludos ni despedidas.")
    typer.secho("🤖 Generando borrador del SMS...", fg=typer.colors.BLUE)
    borrador = generar_idea(prompt)
    typer.secho("---", fg=typer.colors.WHITE)
    typer.secho(f"Borrador generado para {para} ({numero_destinatario}):",
                fg=typer.colors.WHITE)
    typer.secho(borrador, fg=typer.colors.CYAN)
    typer.secho("---", fg=typer.colors.WHITE)
    confirmacion = typer.confirm("¿Quieres enviar este mensaje?")
    if not confirmacion:
        raise typer.Abort()
    try:
        subprocess.run(["termux-sms-send", "-n", numero_destinatario],
                       input=borrador, text=True, check=True)
        typer.echo("✅ SMS enviado con éxito.")
        notificar("AGP CLI", f"SMS enviado a {para}")
    except FileNotFoundError:
        typer.secho("Error: 'termux-sms-send' no encontrado. "
                    "Asegúrate de que Termux:API está instalado y con permisos de SMS.",
                    fg=typer.colors.RED)
    except subprocess.CalledProcessError as e:
        typer.secho(f"Error al enviar el SMS: {e}", fg=typer.colors.RED)
    except Exception as e:
        typer.secho(f"Ha ocurrido un error inesperado: {e}", fg=typer.colors.RED)

@app.command()
def crear_flujo_n8n(descripcion: str):
    """Genera la estructura JSON de un flujo de n8n basado en una descripción."""
    prompt = (
        f"Genera la estructura JSON completa y válida para un flujo de n8n basado "
        f"en la siguiente descripción. Asegúrate de que el JSON sea directamente "
        f"importable en n8n y no incluyas ningún texto adicional, solo el JSON.\n\n"
        f"Descripción: {descripcion}"
    )
    typer.echo("🤖 Generando flujo de n8n...")
    flujo_json_str = generar_idea(prompt)
    try:
        flujo_json = json.loads(flujo_json_str)
        typer.echo("\n--- FLUJO N8N GENERADO (JSON) ---")
        typer.echo(json.dumps(flujo_json, indent=2))
        typer.echo("----------------------------------")
        notificar("AGP CLI", "Flujo n8n generado con éxito.")
    except json.JSONDecodeError:
        typer.echo("Error: La IA no devolvió un JSON válido. "
                   "Intenta refinar la descripción.")
        typer.echo(f"Respuesta de la IA: {flujo_json_str}")
    except Exception as e:
        typer.echo(f"Ha ocurrido un error inesperado: {e}")

@app.command()
def crear_script_python(descripcion: str,
                        nombre_archivo: str = typer.Option("script_generado.py",
                        help="Nombre del archivo .py a crear.")):
    """Genera un script Python basado en una descripción y lo guarda en un archivo."""
    prompt = (
        f"Genera un script completo y funcional en Python para la siguiente descripción. "
        f"El script debe ser autocontenido y no incluir ningún texto adicional, "
        f"solo el código Python.\n\n"
        f"Descripción: {descripcion}"
    )
    typer.echo("🤖 Generando script Python...")
    codigo_python = generar_idea(prompt)
    try:
        with open(nombre_archivo, "w") as f:
            f.write(codigo_python)
        typer.echo(f"✅ Script '{nombre_archivo}' creado con éxito.")
        notificar("AGP CLI", f"Script Python generado: {nombre_archivo}")
    except Exception as e:
        typer.echo(f"Error al guardar el script: {e}")

@app.command(name="crear-archivo", hidden=True)
def _crear_archivo(project_path: str, relative_path: str, content: str = ""):
    """Crea un archivo dentro del directorio del proyecto."""
    try:
        crear_archivo_proyecto(project_path, relative_path, content)
    except Exception as e:
        typer.secho(f"Error al crear archivo: {e}", fg=typer.colors.RED)

@app.command(name="leer-archivo", hidden=True)
def _leer_archivo(project_path: str, relative_path: str):
    """Lee el contenido de un archivo dentro del directorio del proyecto."""
    try:
        leer_archivo_proyecto(project_path, relative_path)
    except Exception as e:
        typer.secho(f"Error al leer archivo: {e}", fg=typer.colors.RED)

@app.command(name="escribir-archivo", hidden=True)
def _escribir_archivo(project_path: str, relative_path: str, content: str):
    """Escribe (sobrescribe) contenido en un archivo dentro del directorio del proyecto."""
    try:
        escribir_archivo_proyecto(project_path, relative_path, content)
    except Exception as e:
        typer.secho(f"Error al escribir archivo: {e}", fg=typer.colors.RED)

@app.command(name="eliminar-archivo", hidden=True)
def _eliminar_archivo(project_path: str, relative_path: str):
    """Elimina un archivo dentro del directorio del proyecto."""
    try:
        eliminar_archivo_proyecto(project_path, relative_path)
    except Exception as e:
        typer.secho(f"Error al eliminar archivo: {e}", fg=typer.colors.RED)

@app.command()
def chat():
    """Inicia un chat interactivo continuo con Gemini. El historial se guarda entre sesiones."""
    typer.secho("Iniciando chat interactivo con Gemini. Di 'salir' para terminar.",
                fg=typer.colors.WHITE)
    history = []
    try:
        with open(CHAT_HISTORY_FILE, "r") as f:
            history = json.load(f)
        typer.secho("(Historial de chat anterior cargado)", fg=typer.colors.WHITE)
    except (FileNotFoundError, json.JSONDecodeError):
        pass
    while True:
        try:
            user_input = listen_and_recognize()
            if user_input and user_input.lower() == "salir":
                break
            elif not user_input:
                continue
            typer.secho("🤖 Pensando...", fg=typer.colors.BLUE)
            history, gemini_response = chat_with_gemini(history, user_input)
            typer.secho(f"Gemini: {gemini_response}", fg=typer.colors.CYAN)
            speak(gemini_response)
            with open(CHAT_HISTORY_FILE, "w") as f:
                json.dump(history, f)
        except Exception as e:
            typer.secho(f"Ha ocurrido un error en el chat: {e}", fg=typer.colors.RED)
            break
    typer.secho("Chat terminado.", fg=typer.colors.WHITE)

@app.command(name="crear-alias")
def crear_alias(nombre: str, comando: str):
    """Crea un alias para un comando o una secuencia de comandos."""
    aliases = _cargar_aliases()
    aliases[nombre] = comando
    _guardar_aliases(aliases)
    typer.echo(f"Alias '{nombre}' creado para el comando: '{comando}'")

@app.command(name="listar-aliases")
def listar_aliases():
    """Muestra todos los alias configurados."""
    aliases = _cargar_aliases()
    if not aliases:
        typer.echo("No hay alias configurados.")
        return
    typer.echo("--- ALIAS DISPONIBLES ---")
    for nombre, comando in aliases.items():
        typer.echo(f"- {nombre}: {comando}")
    typer.echo("-------------------------")

@app.command(name="eliminar-alias")
def eliminar_alias(nombre: str):
    """Elimina un alias."""
    aliases = _cargar_aliases()
    if nombre in aliases:
        del aliases[nombre]
        _guardar_aliases(aliases)
        typer.echo(f"Alias '{nombre}' eliminado.")
    else:
        typer.echo(f"El alias '{nombre}' no existe.")

@app.command(name="aprender")
def aprender(tema: str = typer.Argument(..., help="El tema o habilidad que quieres aprender."),
             objetivo: str = typer.Option(None, "--objetivo",
                                       help="Una descripción clara de lo que quieres lograr.")):
    """Inicia un nuevo proyecto de autoaprendizaje o interactúa con uno existente."""
    aprendizaje_cli_path = "/data/data/com.termux/files/home/.gemini/aprendizaje/aprendizaje_cli.py"
    if objetivo:
        try:
            subprocess.run([aprendizaje_cli_path, "nuevo-proyecto", tema, "--objetivo",
                            objetivo], check=True)
            if typer.confirm(f"¿Quieres que la IA genere un plan de estudio para '{tema}' ahora?"):
                subprocess.run([aprendizaje_cli_path, "crear-plan", tema], check=True)
        except subprocess.CalledProcessError as e:
            typer.echo(f"Error al iniciar el proyecto de aprendizaje: {e}")
        except FileNotFoundError:
            typer.echo(f"Error: No se encontró el script de aprendizaje en {aprendizaje_cli_path}.")
    else:
        typer.echo(f"Para interactuar con el proyecto '{tema}', puedes usar:")
        typer.echo(f"  - `agp aprender {tema} ver-plan`")
        typer.echo(f"  - `agp aprender {tema} marcar-paso-completo <numero>`")
        typer.echo(f"  - `agp aprender {tema} crear-plan` (si aún no tiene uno)")
        typer.echo(f"O ejecuta directamente: `{aprendizaje_cli_path} --help` para ver todos los comandos.")
    notificar("AGP CLI", f"Comando de aprendizaje ejecutado para: {tema}")

@app.command(name="setup")
def setup():
    """Guía de configuración inicial para AGP Gemini CLI. Escribe los valores en el archivo .env."""
    typer.secho("🚀 Iniciando la configuración de AGP Gemini CLI...",
                fg=typer.colors.BRIGHT_MAGENTA)
    typer.secho("Te guiaré a través de los pasos necesarios para configurar el asistente en el archivo .env.",
                fg=typer.colors.WHITE)
    env_vars = _cargar_env()
    typer.secho("\n--- Paso 1: Configuración de la API Key de Gemini ---",
                fg=typer.colors.CYAN)
    typer.secho("Necesitas una API Key de Google Gemini. Puedes obtenerla en: https://aistudio.google.com/app/apikey",
                fg=typer.colors.WHITE)
    gemini_key = typer.prompt("Introduce tu API Key de Gemini",
                              default=env_vars.get("GEMINI_API_KEY", ""))
    env_vars["GEMINI_API_KEY"] = gemini_key
    _guardar_env(env_vars)
    typer.secho("✅ API Key de Gemini guardada en .env.", fg=typer.colors.GREEN)
    typer.secho("\n--- Paso 2: Permisos de Termux:API ---", fg=typer.colors.CYAN)
    typer.secho("Para que el asistente funcione correctamente, Termux y Termux:API necesitan permisos.",
                fg=typer.colors.WHITE)
    typer.secho("Por favor, ve a los Ajustes de Android > Aplicaciones > Termux (y Termux:API).",
                fg=typer.colors.WHITE)
    typer.secho("Asegúrate de que los siguientes permisos estén ACTIVADOS:",
                fg=typer.colors.WHITE)
    typer.secho("  - Micrófono (para comandos de voz)", fg=typer.colors.WHITE)
    typer.secho("  - Ubicación (para notas rápidas con geolocalización)",
                fg=typer.colors.WHITE)
    typer.secho("  - Contactos (para buscar contactos para SMS)",
                fg=typer.colors.WHITE)
    typer.secho("  - Cámara (para análisis de fotos)", fg=typer.colors.WHITE)
    typer.secho("  - Teléfono/SMS (para enviar SMS)", fg=typer.colors.WHITE)
    typer.confirm("¿Has revisado y configurado los permisos?", abort=True)
    typer.secho("✅ Permisos confirmados.", fg=typer.colors.GREEN)
    typer.secho("\n--- Paso 3: Configuración de GitHub (Opcional) ---",
                fg=typer.colors.CYAN)
    if typer.confirm("¿Quieres configurar tu Personal Access Token de GitHub ahora?"):
        typer.secho("Necesitas un Personal Access Token (PAT) de GitHub con permisos de 'repo'.",
                    fg=typer.colors.WHITE)
        typer.secho("Puedes crearlo en: https://github.com/settings/tokens",
                    fg=typer.colors.WHITE)
        github_token = typer.prompt("Introduce tu Personal Access Token de GitHub",
                                  default=env_vars.get("GITHUB_TOKEN", ""))
        env_vars["GITHUB_TOKEN"] = github_token
        _guardar_env(env_vars)
        typer.secho("✅ Token de GitHub guardado en .env.", fg=typer.colors.GREEN)
    else:
        typer.echo("Configuración de GitHub omitida por ahora.")
    typer.secho("\n--- Paso 4: Verificación de Alias y Ejecutables ---",
                fg=typer.colors.CYAN)
    typer.secho("Asegúrate de que el alias `agp` y el comando `mcp` estén disponibles.",
                fg=typer.colors.WHITE)
    typer.secho("Si no lo están, ejecuta `bash /data/data/com.termux/files/home/agp-gemini-cli/setup.sh` y reinicia tu terminal.",
                fg=typer.colors.WHITE)
    typer.secho("✅ Configuración inicial completada. ¡Ya puedes usar AGP Gemini CLI!",
                fg=typer.colors.BRIGHT_GREEN)
    notificar("AGP CLI", "Configuración inicial completada.")

@app.command(name="ver-config")
def ver_config():
    """Muestra la configuración actual cargada desde las variables de entorno."""
    typer.secho("--- CONFIGURACIÓN ACTUAL (desde variables de entorno) ---",
                fg=typer.colors.BRIGHT_MAGENTA)
    gemini_key = os.environ.get("GEMINI_API_KEY")
    github_token = os.environ.get("GITHUB_TOKEN")
    typer.secho(f"GEMINI_API_KEY: {'*' * (len(gemini_key) - 4) + gemini_key[-4:] if gemini_key else 'No configurada'}",
                fg=typer.colors.WHITE)
    typer.secho(f"GITHUB_TOKEN: {'*' * (len(github_token) - 4) + github_token[-4:] if github_token else 'No configurado'}",
                fg=typer.colors.WHITE)
    typer.secho("----------------------------------------------------",
                fg=typer.colors.BRIGHT_MAGENTA)

@app.command(name="iniciar-proyecto")
def iniciar_proyecto(
    descripcion: str,
    init_git: bool = typer.Option(False, "--git", "-g",
                               help="Inicializar un repositorio Git local."),
    create_github_repo: bool = typer.Option(False, "--github", "-gh",
                                         help="Crear un repositorio remoto en GitHub."),
    github_repo_name: str = typer.Option(None, "--github-name",
                                       help="Nombre del repositorio en GitHub (por defecto, el nombre del proyecto)."),
    github_repo_private: bool = typer.Option(False, "--github-private",
                                           help="Hacer el repositorio de GitHub privado.")
):
    """Inicia una sesión interactiva con el Asistente de Proyectos de IA."""
    typer.secho("Iniciando Asistente de Proyectos...", fg=typer.colors.BRIGHT_MAGENTA)
    # ... (resto del código de iniciar_proyecto)

def main():
    aliases = _cargar_aliases()
    if len(sys.argv) > 1 and sys.argv[1] in aliases:
        alias_cmd = aliases[sys.argv[1]]
        sys.argv = [sys.argv[0]] + alias_cmd.split() + sys.argv[2:]
    app()

if __name__ == "__main__":
    main()