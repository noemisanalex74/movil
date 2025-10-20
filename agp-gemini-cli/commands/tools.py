
import json
import os
import subprocess

import typer
from gemini_interface import analizar_imagen_con_gemini, generar_idea

tools_app = typer.Typer(
    name="tools", help="Herramientas y scripts experimentales."
)

CUSTOM_TOOLS_DIR = "/data/data/com.termux/files/home/agp-gemini-cli/custom_tools"


@tools_app.command(name="live-stream-test")
def run_live_stream_test():
    """
    Ejecuta el script de ejemplo de Gemini Live API (streaming).
    """
    script_path = os.path.join(CUSTOM_TOOLS_DIR, "live_api_streaming_example.py")
    if not os.path.exists(script_path):
        typer.secho(
            f"Error: No se encuentra el script en {script_path}",
            fg=typer.colors.RED
        )
        raise typer.Abort()

    typer.echo("🚀 Ejecutando el script de prueba de Gemini Live API...")
    try:
        subprocess.run(["python", script_path], check=True)
    except subprocess.CalledProcessError as e:
        typer.secho(
            f"El script terminó con un error:\n{e}", fg=typer.colors.RED
        )
    except Exception as e:
        typer.secho(f"Ocurrió un error inesperado: {e}", fg=typer.colors.RED)


@tools_app.command(name="mcp-server-test")
def run_mcp_server_test():
    """
    Ejecuta el servidor de ejemplo para Model Context Protocol (MCP).
    """
    script_path = os.path.join(CUSTOM_TOOLS_DIR, "mcp_server_example.py")
    if not os.path.exists(script_path):
        typer.secho(
            f"Error: No se encuentra el script en {script_path}",
            fg=typer.colors.RED
        )
        raise typer.Abort()

    typer.echo("🚀 Ejecutando el servidor de prueba MCP...")
    typer.echo("El servidor se iniciará en http://127.0.0.1:8000")
    typer.echo("Presiona Ctrl+C para detenerlo.")
    try:
        subprocess.run(["python", script_path], check=True)
    except KeyboardInterrupt:
        typer.secho(
            "\nServidor detenido por el usuario.", fg=typer.colors.YELLOW
        )
    except Exception as e:
        typer.secho(f"Ocurrió un error inesperado: {e}", fg=typer.colors.RED)


@tools_app.command(name="analizar-foto")
def analizar_foto(
    prompt: str = typer.Option(
        "Describe la imagen en detalle.",
        "--prompt",
        "-p",
        help="Pregunta específica sobre la foto.",
    )
):
    """
    Toma una foto con la cámara y la analiza con Gemini.
    """
    temp_photo_path = "/data/data/com.termux/files/home/temp_photo.jpg"
    typer.echo("📸 Preparando la cámara...")

    try:
        # Tomar la foto usando Termux:API y redirigiendo la salida
        subprocess.run(
            f"termux-camera-photo > {temp_photo_path}", shell=True, check=True
        )

        if not os.path.exists(temp_photo_path) or os.path.getsize(
            temp_photo_path
        ) == 0:
            typer.secho(
                "Error: No se pudo guardar la foto. ¿Cancelaste la captura?",
                fg=typer.colors.RED,
            )
            raise typer.Abort()

        typer.echo("🤖 Analizando la imagen con Gemini...")
        analisis = analizar_imagen_con_gemini(
            image_path=temp_photo_path, prompt=prompt
        )

        typer.secho("\n--- ANÁLISIS DE LA IMAGEN ---", fg=typer.colors.CYAN)
        typer.echo(analisis)
        typer.secho("-----------------------------", fg=typer.colors.CYAN)

    except FileNotFoundError:
        typer.secho(
            "Error: 'termux-camera-photo' no encontrado. "
            "Asegúrate de que Termux:API está instalado y con permisos de cámara.",
            fg=typer.colors.RED,
        )
    except subprocess.CalledProcessError as e:
        typer.secho(f"Error al usar la cámara: {e.stderr}", fg=typer.colors.RED)
    except Exception as e:
        typer.secho(f"Ocurrió un error inesperado: {e}", fg=typer.colors.RED)
    finally:
        # Limpiar la foto temporal
        if os.path.exists(temp_photo_path):
            os.remove(temp_photo_path)
            typer.echo("\n(Imagen temporal eliminada)")


@tools_app.command(name="bateria")
def consultar_bateria(
    ia: bool = typer.Option(
        False,
        "--ia",
        help="Añade un comentario de la IA sobre el estado de la batería.",
    )
):
    """
    Muestra el estado de la batería del dispositivo.
    """
    try:
        result = subprocess.run(
            ["termux-battery-status"],
            capture_output=True,
            text=True,
            check=True
        )
        status = json.loads(result.stdout)

        percentage = status.get("percentage", "N/A")
        plugged = status.get("plugged", "N/A")
        health = status.get("health", "N/A")
        temperature = status.get("temperature", "N/A")

        typer.secho("🔋 Estado de la Batería 🔋", fg=typer.colors.GREEN)
        typer.echo(f"- Nivel: {percentage}%")
        typer.echo(f"- Conectado: {plugged}")
        typer.echo(f"- Salud: {health}")
        typer.echo(f"- Temperatura: {temperature}°C")

        if ia:
            typer.echo("🤖 Generando comentario de la IA...")
            prompt = (
                f"Basado en este estado de la batería (Nivel: {percentage}%, "
                f"Conectado: {plugged}, Salud: {health}), dame un comentario "
                f"muy breve y útil en una sola frase."
            )
            comentario = generar_idea(prompt)
            typer.secho(f"\nComentario IA: {comentario}", fg=typer.colors.CYAN)

    except FileNotFoundError:
        typer.secho(
            "Error: 'termux-battery-status' no encontrado. "
            "Asegúrate de que Termux:API está instalado.",
            fg=typer.colors.RED,
        )
    except (subprocess.CalledProcessError, json.JSONDecodeError) as e:
        typer.secho(
            f"Error al obtener o procesar el estado de la batería: {e}",
            fg=typer.colors.RED,
        )
    except Exception as e:
        typer.secho(f"Ocurrió un error inesperado: {e}", fg=typer.colors.RED)


@tools_app.command(name="ubicacion")
def consultar_ubicacion(
    ia: bool = typer.Option(
        False, "--ia", help="Añade un análisis de la IA sobre la ubicación."
    ),
    prompt_ia: str = typer.Option(
        "Describe el contexto de esta ubicación y sugiere algo interesante que "
        "hacer aquí.",
        "--prompt-ia",
        "-p",
        help="Prompt específico para la IA sobre la ubicación.",
    ),
):
    """
    Muestra la ubicación actual del dispositivo y opcionalmente la analiza con Gemini.
    """
    try:
        typer.echo("📍 Obteniendo ubicación...")
        result = subprocess.run(
            ["termux-location"], capture_output=True, text=True, check=True
        )
        location_data = json.loads(result.stdout)

        latitude = location_data.get("latitude", "N/A")
        longitude = location_data.get("longitude", "N/A")
        accuracy = location_data.get("accuracy", "N/A")
        timestamp = location_data.get("timestamp", "N/A")

        typer.secho("\n--- Ubicación Actual ---", fg=typer.colors.GREEN)
        typer.echo(f"- Latitud: {latitude}")
        typer.echo(f"- Longitud: {longitude}")
        typer.echo(f"- Precisión: {accuracy} metros")
        typer.echo(f"- Hora: {timestamp}")

        if ia:
            typer.echo("🤖 Analizando ubicación con Gemini...")
            full_prompt = (
                f"Basado en esta ubicación (Latitud: {latitude}, "
                f"Longitud: {longitude}, Precisión: {accuracy} metros, "
                f"Hora: {timestamp}), {prompt_ia}"
            )
            analisis_ia = generar_idea(full_prompt)
            typer.secho(f"\nComentario IA: {analisis_ia}", fg=typer.colors.CYAN)

    except FileNotFoundError:
        typer.secho(
            "Error: 'termux-location' no encontrado. "
            "Asegúrate de que Termux:API está instalado y con permisos de ubicación.",
            fg=typer.colors.RED,
        )
    except (subprocess.CalledProcessError, json.JSONDecodeError) as e:
        typer.secho(
            f"Error al obtener o procesar la ubicación: {e}", fg=typer.colors.RED
        )
    except Exception as e:
        typer.secho(f"Ocurrió un error inesperado: {e}", fg=typer.colors.RED)


@tools_app.command(name="notificaciones")
def consultar_notificaciones(
    resumir: bool = typer.Option(
        False,
        "--resumir",
        "-r",
        help="Pide a la IA que resuma las notificaciones.",
    )
):
    """
    Muestra las notificaciones recientes del dispositivo y opcionalmente las resume
    con Gemini.
    """
    try:
        typer.echo("🔔 Obteniendo notificaciones...")
        result = subprocess.run(
            ["termux-notification-list"], capture_output=True, text=True, check=True
        )
        notifications_data = json.loads(result.stdout)

        if not notifications_data:
            typer.echo("No hay notificaciones recientes.")
            return

        typer.secho("\n--- Notificaciones Recientes ---", fg=typer.colors.GREEN)
        notifications_text = []
        for i, notif in enumerate(notifications_data):
            title = notif.get("title", "Sin título")
            content = notif.get("content", "Sin contenido")
            package = notif.get("package", "Desconocido")
            post_time = notif.get("post_time", "N/A")

            notification_summary = (
                f"[{i+1}] {title} ({package}) - {content} (Hora: {post_time})"
            )
            typer.echo(notification_summary)
            notifications_text.append(notification_summary)

        if resumir:
            typer.echo("🤖 Resumiendo notificaciones con Gemini...")
            full_prompt = (
                "Resume y prioriza las siguientes notificaciones de un usuario de "
                "Android. Identifica las más importantes y sugiere acciones si es "
                f"pertinente. Notificaciones: {'\n'.join(notifications_text)}"
            )
            resumen_ia = generar_idea(full_prompt)
            typer.secho(f"\nResumen IA: {resumen_ia}", fg=typer.colors.CYAN)

    except FileNotFoundError:
        typer.secho(
            "Error: 'termux-notification-list' no encontrado. Asegúrate de que "
            "Termux:API está instalado y con permisos de notificaciones.",
            fg=typer.colors.RED,
        )
    except (subprocess.CalledProcessError, json.JSONDecodeError) as e:
        typer.secho(
            f"Error al obtener o procesar las notificaciones: {e}",
            fg=typer.colors.RED,
        )
    except Exception as e:
        typer.secho(f"Ocurrió un error inesperado: {e}", fg=typer.colors.RED)
