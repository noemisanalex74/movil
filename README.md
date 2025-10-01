# Proyecto de Automatización y Gestión Personal (AGP)

Este proyecto es un sistema integral diseñado para la automatización de tareas y procesos, con un enfoque particular en la gestión remota de operaciones empresariales y la optimización de la productividad personal en entornos móviles (Termux).

## Componentes Principales

El proyecto AGP se compone de varias herramientas interconectadas:

1.  **AGP Dashboard Web (`agp-dashboard-web`):** Una interfaz web para la gestión centralizada de proyectos, tareas, herramientas personalizadas (MCPs) y la monitorización de agentes empresariales.
2.  **AGP Gemini CLI (`agp-gemini-cli`):** Una herramienta de línea de comandos para interactuar con el sistema, incluyendo la integración con la API de Gemini para generación de contenido y la ejecución de comandos experimentales.
3.  **AGP Enterprise Agent (`agp-enterprise-agent`):** Un agente ligero y seguro diseñado para ser desplegado en sistemas de empresas cliente, facilitando la comunicación y la ejecución remota de automatizaciones.

## Características Destacadas

### AGP Dashboard Web
*   **Menú de Hamburguesa y Mejoras Visuales:** Navegación lateral y estética mejorada.
*   **Visualización y Gestión de Proyectos:** Sección para mostrar y buscar datos de `proyectos.json`.
*   **Gestión de Herramientas Personalizadas (MCP):** Funcionalidad CRUD completa (Crear, Leer, Actualizar, Eliminar) con paginación y búsqueda.
*   **Gestión de Tareas:** Funcionalidad CRUD para tareas, con paginación y búsqueda.
*   **Gestión de Ajustes (Settings):** Página para configurar API Keys y Tokens.
*   **Visor de Logs Integrado:** Acceso a los logs del servidor Flask.
*   **Ejecución de Comandos del CLI:** Permite ejecutar comandos de shell y ver su salida.
*   **Diseño Responsivo Avanzado:** Optimizado para diferentes dispositivos.
*   **Exportación de Datos:** Exportación de tareas, proyectos y MCPs a CSV.
*   **Notificaciones en el Dashboard:** Mensajes flash para operaciones CRUD.
*   **Autenticación y Autorización de Usuarios:** Sistema de inicio de sesión con Flask-Login.
*   **Integración de Bootstrap:** Interfaz de usuario mejorada con Bootstrap 5.
*   **Gráficos y Estadísticas de Proyectos:** Visualización de estadísticas con Chart.js.
*   **Notificaciones en Tiempo Real:** Sistema de notificaciones con Flask-SocketIO.
*   **Confirmación de Eliminación con Modal:** Modales de Bootstrap para confirmaciones.
*   **Mejora de Formularios:** Formularios con clases de Bootstrap y validación.
*   **Alternar Modo Oscuro/Claro:** Personalización del tema de la interfaz.
*   **Resumen General del Dashboard Dinámico:** Métricas clave en la página principal.
*   **Registro de Fecha de Modificación de Tareas:** Seguimiento automático de la última modificación.
*   **Tablero Kanban para Tareas:** Vista visual de tareas con arrastrar y soltar.

### AGP Gemini CLI
*   **Investigación de Model Context Protocol (MCP):** Servidor de ejemplo con FastAPI y fastmcp.
*   **Integración de Gemini Live API (Streaming):** Generación de texto en streaming, con solución a problemas de compilación de `grpcio` en Termux.
*   **Nuevos Comandos `tools`:** Comandos `live-stream-test` y `mcp-server-test`.

## Visión a Largo Plazo

El objetivo es desarrollar un sistema robusto para la automatización de tareas y procesos en diferentes empresas de forma remota, priorizando la adaptabilidad a entornos móviles y el uso de herramientas gratuitas. Para más detalles, consulta `VISION.md`.

## Instalación y Uso (en Termux)

El proyecto está diseñado para ser ejecutado en Termux en un dispositivo móvil.

### Requisitos Previos
*   Termux instalado en tu dispositivo Android.
*   Python 3 y Poetry (gestor de dependencias) instalados en Termux.

### Configuración Inicial
1.  Clona este repositorio:
    ```bash
    git clone [URL_DEL_REPOSITORIO]
    cd agp-project-root
    ```
2.  Instala las dependencias para cada subproyecto (ejemplo para `agp-dashboard-web`):
    ```bash
    cd agp-dashboard-web
    poetry install
    cd ..
    # Repite para agp-gemini-cli y agp-enterprise-agent si es necesario
    ```

### Iniciar el Dashboard Web
Para iniciar el dashboard web, utiliza el script de inicio corregido:
```bash
~/.shortcuts/start_agp_dashboard.sh
```
Este script asegura que el entorno virtual y las dependencias correctas sean utilizadas.

## Contribución

¡Las contribuciones son bienvenidas! Por favor, consulta `CONTRIBUTING.md` para más detalles.
