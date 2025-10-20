

import google.generativeai as genai


def run_streaming_example():
    """
    Ejemplo de cómo generar texto en tiempo real (streaming) con la API de Gemini.
    """
    try:
        # La API Key se puede configurar como variable de entorno GOOGLE_API_KEY
        # genai.configure(api_key="YOUR_API_KEY")

        print("Inicializando el modelo Gemini...")
        model = genai.GenerativeModel('models/gemini-flash-latest')

        prompt = "Hola Gemini, cuéntame una historia corta y sorprendente."
        print(f"\nEnviando prompt: '{prompt}'\n")
        
        response = model.generate_content(prompt, stream=True)

        print("Respuesta del modelo (en tiempo real):")
        for chunk in response:
            print(chunk.text, end="", flush=True)
        print("\n\nFinalizado.")

    except Exception as e:
        print(f"Ha ocurrido un error: {e}")
        print("Asegúrate de que tu API Key de Google esté configurada correctamente.")
        print("Puedes hacerlo ejecutando: export GOOGLE_API_KEY='TU_API_KEY'")

if __name__ == "__main__":
    run_streaming_example()

