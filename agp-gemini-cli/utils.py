import os
import subprocess

import requests
import speech_recognition as sr
import typer
from bs4 import BeautifulSoup
from gtts import gTTS
from pydub import AudioSegment
from pydub.playback import play


def notificar(titulo, mensaje):
    """
    Envía una notificación nativa a través de Termux:API.
    """
    try:
        subprocess.run(
            ["termux-notification", "--title", titulo, "--content", mensaje], check=True
        )
    except FileNotFoundError:
        # Esto ocurre si termux-api no está instalado o accesible.
        # Podemos imprimir un mensaje en la consola en lugar de fallar.
        print(
            "\n[Advertencia: No se pudo enviar la notificación. Asegúrate de que Termux:API esté instalado y configurado.]"
        )
    except Exception as e:
        # Captura otros posibles errores
        print(f"\n[Error al enviar notificación: {e}]")


def listen_and_recognize():
    """
    Escucha el micrófono y reconoce el habla.
    Retorna el texto reconocido o None si hay un error.
    """
    r = sr.Recognizer()
    print("Intentando inicializar micrófono...")
    try:
        with sr.Microphone() as source:
            print("Micrófono inicializado. Escuchando...")
            audio = r.listen(source, timeout=5, phrase_time_limit=5)
            print("Audio capturado. Reconociendo...")
    except Exception as e:
        print(f"Error al inicializar o escuchar el micrófono: {e}")
        return None

    try:
        text = r.recognize_google(audio, language="es-ES")
        print(f"Has dicho: {text}")
        return text
    except sr.WaitTimeoutError:
        print("No se detectó habla.")
        return None
    except sr.UnknownValueError:
        print("No se pudo entender el audio.")
        return None
    except sr.RequestError as e:
        print(f"Error en el servicio de reconocimiento de voz; {e}")
        return None


def speak(text):
    """
    Convierte texto a voz y lo reproduce.
    """
    try:
        tts = gTTS(text=text, lang="es", slow=False)
        temp_file = "temp_audio.mp3"
        tts.save(temp_file)
        audio = AudioSegment.from_mp3(temp_file)
        play(audio)
        os.remove(temp_file)
    except Exception as e:
        print(f"Error al reproducir audio: {e}")


def extraer_texto_de_url(url: str) -> str:
    """
    Descarga el contenido de una URL y extrae el texto limpio.
    """
    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        }
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()

        soup = BeautifulSoup(response.content, "lxml")

        # Eliminar elementos no deseados
        for script_or_style in soup(
            ["script", "style", "header", "footer", "nav", "aside"]
        ):
            script_or_style.decompose()

        # Extraer texto y limpiar
        text = soup.get_text(separator="\n", strip=True)
        return text

    except requests.exceptions.RequestException as e:
        return f"Error al descargar la URL: {e}"
    except Exception as e:
        return f"Error al procesar el contenido HTML: {e}"


# --- Funciones de Gestión de Archivos de Proyecto ---


def _get_full_path(project_path: str, relative_path: str) -> str:
    """
    Obtiene la ruta completa de un archivo dentro del directorio del proyecto.
    """
    full_path = os.path.join(project_path, relative_path)
    # Asegurarse de que la ruta resultante esté dentro del directorio del proyecto
    if not os.path.abspath(full_path).startswith(os.path.abspath(project_path)):
        raise ValueError("Operación fuera del directorio del proyecto no permitida.")
    return full_path


def crear_archivo_proyecto(project_path: str, relative_path: str, content: str):
    """
    Crea un nuevo archivo dentro del directorio del proyecto.
    """
    full_path = _get_full_path(project_path, relative_path)
    os.makedirs(os.path.dirname(full_path), exist_ok=True)
    with open(full_path, "w") as f:
        f.write(content)
    typer.secho(
        f"✅ Archivo '{relative_path}' creado en '{project_path}'.",
        fg=typer.colors.GREEN,
    )


def leer_archivo_proyecto(project_path: str, relative_path: str) -> str:
    """
    Lee el contenido de un archivo dentro del directorio del proyecto.
    """
    full_path = _get_full_path(project_path, relative_path)
    if not os.path.exists(full_path):
        typer.secho(
            f"Error: El archivo '{relative_path}' no existe en '{project_path}'.",
            fg=typer.colors.RED,
        )
        raise FileNotFoundError
    with open(full_path, "r") as f:
        content = f.read()
    typer.echo(f"--- Contenido de '{relative_path}' ---")
    typer.echo(content)
    typer.echo("----------------------------------")
    return content


def escribir_archivo_proyecto(project_path: str, relative_path: str, content: str):
    """
    Escribe (sobrescribe) contenido en un archivo dentro del directorio del proyecto.
    Pide confirmación si el archivo ya existe.
    """
    full_path = _get_full_path(project_path, relative_path)
    if os.path.exists(full_path):
        if not typer.confirm(f"El archivo '{relative_path}' ya existe. ¿Sobrescribir?"):
            typer.echo("Operación cancelada.")
            raise typer.Abort()
    os.makedirs(os.path.dirname(full_path), exist_ok=True)
    with open(full_path, "w") as f:
        f.write(content)
    typer.secho(
        f"✅ Archivo '{relative_path}' actualizado en '{project_path}'.",
        fg=typer.colors.GREEN,
    )


def eliminar_archivo_proyecto(project_path: str, relative_path: str):
    """
    Elimina un archivo dentro del directorio del proyecto.
    Pide confirmación antes de eliminar.
    """
    full_path = _get_full_path(project_path, relative_path)
    if not os.path.exists(full_path):
        typer.secho(
            f"Error: El archivo '{relative_path}' no existe en '{project_path}'.",
            fg=typer.colors.RED,
        )
        raise FileNotFoundError

    if typer.confirm(
        f"¿Estás seguro de que quieres eliminar '{relative_path}' de '{project_path}'? Esta acción es irreversible."
    ):
        os.remove(full_path)
        typer.secho(
            f"✅ Archivo '{relative_path}' eliminado de '{project_path}'.",
            fg=typer.colors.GREEN,
        )
    else:
        typer.echo("Operación cancelada.")
        raise typer.Abort()
