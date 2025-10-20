import os

import google.generativeai as genai
import typer
from dotenv import load_dotenv
from PIL import Image

# Variable para asegurar que la configuración se haga solo una vez
_is_configured = False

def configure_genai():
    """
    Configura la API de Gemini. Busca la clave en las variables de entorno.
    Si no la encuentra, la solicita al usuario.
    """
    global _is_configured
    if _is_configured:
        return

    load_dotenv()  # Carga el archivo .env si existe
    api_key = os.environ.get("GEMINI_API_KEY")

    if not api_key:
        typer.secho("API Key de Gemini no encontrada.", fg=typer.colors.YELLOW)
        api_key = typer.prompt("Por favor, introduce tu API Key de Gemini", hide_input=True)
        if not api_key:
            typer.secho("Operación cancelada. Se requiere una API Key.", fg=typer.colors.RED)
            raise typer.Abort()
        
        # Configurar solo para la sesión actual
        genai.configure(api_key=api_key)
        typer.secho("API Key configurada para la sesión actual.", fg=typer.colors.GREEN)
        typer.echo("Para guardarla permanentemente, ejecuta: agp setup")
    else:
        genai.configure(api_key=api_key)
    
    _is_configured = True

def generar_idea(prompt: str, modelo: str = 'models/gemini-flash-latest'):
    """
    Genera contenido de texto usando un modelo de Gemini.
    """
    configure_genai()
    try:
        model = genai.GenerativeModel(modelo)
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        # Captura errores de la API de forma más específica si es posible
        typer.secho(f"Error al generar idea con Gemini: {e}", fg=typer.colors.RED)
        return "No se pudo generar una respuesta."

def chat_with_gemini(history: list, new_message: str):
    """
    Mantiene una conversación con Gemini, gestionando el historial.
    """
    configure_genai()
    try:
        model = genai.GenerativeModel('gemini-pro')
        chat = model.start_chat(history=history)
        response = chat.send_message(new_message)
        return chat.history, response.text
    except Exception as e:
        typer.secho(f"Error en el chat con Gemini: {e}", fg=typer.colors.RED)
        return history, "No se pudo obtener una respuesta del chat."

def analizar_imagen_con_gemini(image_path: str, prompt: str):
    """
    Analiza una imagen con un prompt de texto usando el modelo de visión de Gemini.
    """
    configure_genai()
    try:
        img = Image.open(image_path)
        model = genai.GenerativeModel('gemini-pro-vision')
        response = model.generate_content([prompt, img])
        return response.text
    except FileNotFoundError:
        typer.secho(f"Error: No se encontró el archivo de imagen en {image_path}", fg=typer.colors.RED)
        return "Análisis fallido: archivo no encontrado."
    except Exception as e:
        typer.secho(f"Error al analizar la imagen con Gemini: {e}", fg=typer.colors.RED)
        return "No se pudo completar el análisis de la imagen."