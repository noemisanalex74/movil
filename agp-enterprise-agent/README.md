# AGP Enterprise Agent

El **AGP Enterprise Agent** es un componente ligero y seguro del ecosistema AGP, diseñado para ser desplegado en sistemas de empresas cliente (servidores, PCs, etc.). Su función principal es actuar como un punto de ejecución remoto para las automatizaciones orquestadas desde el AGP Dashboard Web, siguiendo un modelo de seguridad Zero Trust.

## Características Principales

*   **Conectividad Segura:** Establece conexiones seguras con el AGP Dashboard Web utilizando WebSockets seguros (WSS) y autenticación mTLS (autenticación mutua de certificados), garantizando la confidencialidad e integridad de las comunicaciones.
*   **Ejecución Remota de Comandos:** Recibe y ejecuta comandos y tareas definidas en Playbooks enviados desde el dashboard.
*   **Lista Blanca de Comandos:** Implementa una estricta política de seguridad mediante un archivo `allowed_commands.json`, que define explícitamente qué comandos puede ejecutar el agente y con qué argumentos, minimizando riesgos de ejecución no autorizada.
*   **Reporte de Estado (Heartbeats):** Envía periódicamente señales de vida (heartbeats) al dashboard para informar sobre su estado (online/offline) y disponibilidad.
*   **Diseño Ligero:** Optimizado para un bajo consumo de recursos, lo que permite su despliegue en una amplia variedad de entornos.
*   **Multiplataforma:** Desarrollado en Python con `asyncio`, lo que facilita su ejecución en diferentes sistemas operativos.

## Instalación y Uso

Para instalar las dependencias y usar el AGP Enterprise Agent:

1.  **Navegar al Directorio del Agente:**
    ```bash
    cd /data/data/com.termux/files/home/agp-enterprise-agent
    ```
2.  **Instalar Dependencias con Poetry:**
    ```bash
    poetry install
    ```
3.  **Configuración:**
    Antes de iniciar el agente, es necesario configurar las variables de entorno y el archivo `allowed_commands.json`. Consulta la [Guía de Despliegue y Configuración del AGP Dashboard y Agente Enterprise](../agp-dashboard-web/DEPLOYMENT.md) para obtener detalles completos sobre la configuración.

4.  **Iniciar el Agente:**
    Una vez configurado, puedes iniciar el agente:
    ```bash
    poetry run python main.py
    ```
    El agente intentará conectarse al dashboard utilizando la configuración proporcionada.

## Seguridad

La seguridad es un pilar fundamental del AGP Enterprise Agent. Se basa en:
*   **Zero Trust Network Access (ZTNA):** Acceso granular y verificado continuamente.
*   **mTLS:** Autenticación mutua de certificados para todas las comunicaciones.
*   **Lista Blanca de Comandos:** Control estricto sobre las operaciones permitidas.

Es crucial mantener el archivo `allowed_commands.json` actualizado y revisado, y asegurar que las credenciales (`AGP_AGENT_ID`, `AGP_AUTH_TOKEN`) se gestionen de forma segura.

## Contribución

Las contribuciones al AGP Enterprise Agent son bienvenidas. Por favor, consulta la documentación general del proyecto y el `CONTRIBUTING.md` (si existe) para más detalles.
