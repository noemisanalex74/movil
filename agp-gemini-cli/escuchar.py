from gemini_interface import generar_idea
from utils import listen_and_recognize, speak


def escuchar_y_responder():
    """
    Activa el micrófono, reconoce el habla, envía el texto a Gemini
    y reproduce la respuesta.
    """
    texto_reconocido = listen_and_recognize()

    if texto_reconocido:
        print(f"Texto reconocido (en minúsculas): {texto_reconocido.lower()}")
        if texto_reconocido.lower().startswith(
            "gemini"
        ) or texto_reconocido.lower().startswith("géminis"):
            speak("si alejandro estoy aqui dime en que puedo ayudarte?")
            return  # Termina la función aquí para no generar otra respuesta
        print("🤖 Pensando...")
        respuesta = generar_idea(texto_reconocido)
        print(f"\n💡 Respuesta de Gemini:\n{respuesta}")
        speak(respuesta)
    else:
        print("No se reconoció ningún texto o hubo un error en el reconocimiento.")


if __name__ == "__main__":
    escuchar_y_responder()
