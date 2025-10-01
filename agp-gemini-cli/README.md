# AGP Gemini CLI

La **AGP Gemini CLI** es la interfaz de línea de comandos principal del proyecto AGP, diseñada para facilitar el desarrollo, la gestión y el bootstrapping de todo el ecosistema. Actúa como una herramienta versátil para interactuar con los diversos componentes de la plataforma, incluyendo la integración con modelos de IA y la ejecución de comandos experimentales.

## Características Principales

*   **Integración con Gemini Live API (Streaming):** Permite la generación de texto en tiempo real utilizando la API de Gemini, con optimizaciones para entornos móviles como Termux.
*   **Comandos de Herramientas (Tools):** Un grupo de comandos dedicado a funcionalidades experimentales y de prueba, incluyendo:
    *   `live-stream-test`: Para probar la generación de texto en streaming.
    *   `mcp-server-test`: Para experimentar con el Model Context Protocol (MCP).
*   **Investigación de Model Context Protocol (MCP):** Soporte y herramientas para la investigación y desarrollo de MCP, incluyendo un servidor de ejemplo con FastAPI y fastmcp.
*   **Utilidades de Desarrollo:** Funciones para la actualización automática, gestión de archivos y otras utilidades que apoyan el desarrollo del proyecto.

## Instalación y Uso

Para instalar las dependencias y usar la AGP Gemini CLI:

1.  **Navegar al Directorio del CLI:**
    ```bash
    cd /data/data/com.termux/files/home/agp-gemini-cli
    ```
2.  **Instalar Dependencias con Poetry:**
    ```bash
    poetry install
    ```
3.  **Ejecutar Comandos:**
    Puedes ejecutar comandos usando `poetry run agp <comando>` o, si has activado el entorno virtual (`poetry shell`), simplemente `agp <comando>`.

    Ejemplos:
    ```bash
    poetry run agp tools live-stream-test
    poetry run agp tools mcp-server-test
    ```

## Contribución

Las contribuciones a la AGP Gemini CLI son bienvenidas. Por favor, consulta la documentación general del proyecto y el `CONTRIBUTING.md` (si existe) para más detalles.
