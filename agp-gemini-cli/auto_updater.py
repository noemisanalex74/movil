import json


def analizar_y_actualizar_prompt():
    """
    Analiza el historial de comandos para identificar patrones
    y potencialmente auto-mejorar el prompt del sistema o las preferencias.
    """
    try:
        with open(
            "/data/data/com.termux/files/home/agp-gemini-cli/context_memory.json", "r+"
        ) as f:
            contexto = json.load(f)

            # Ejemplo de lógica de aprendizaje simple:
            # Si un tema se repite, se podría añadir a las preferencias.
            comandos = contexto.get("últimos_comandos", [])
            temas = {}
            for cmd in comandos:
                if "automatizar" in cmd:
                    temas["automatizar"] = temas.get("automatizar", 0) + 1

            if temas.get("automatizar", 0) > 3:
                if "automatización" not in contexto["preferencias"].get("enfoque", ""):
                    print(
                        "Aprendizaje: El usuario se enfoca mucho en la automatización. Actualizando preferencias."
                    )
                    contexto["preferencias"]["enfoque"] += ", automatización avanzada"

                    # Volver al inicio del archivo para sobreescribir
                    f.seek(0)
                    json.dump(contexto, f, indent=2)
                    f.truncate()

    except FileNotFoundError:
        print("No se encontró el archivo de contexto.")


if __name__ == "__main__":
    analizar_y_actualizar_prompt()
