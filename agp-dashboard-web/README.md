# AGP Dashboard Web

El **AGP Dashboard Web** es la interfaz central y el centro de control de la Plataforma de Automatización y Gestión Personal (AGP). Desarrollado con Flask y Bootstrap 5, proporciona una potente herramienta para la gestión, monitorización y orquestación de tareas y agentes en el ecosistema AGP. Está diseñado para ser responsivo y funcional en diversos dispositivos, incluyendo entornos móviles a través de Termux.

## Características Principales

El dashboard ofrece una amplia gama de funcionalidades para una gestión eficiente:

*   **Gestión de Agentes:** Registro, listado y monitorización del estado de los agentes remotos.
*   **Motor de Playbooks:** Creación, gestión y ejecución de Playbooks de automatización (en formato YAML) sobre agentes específicos.
*   **Gestión de Tareas y Proyectos:** Funcionalidades CRUD completas para organizar y seguir el progreso de tareas y proyectos, incluyendo un **Tablero Kanban** interactivo.
*   **Gestión de Herramientas Personalizadas (MCP):** Administración de MCPs con operaciones CRUD.
*   **Gestión de Ajustes:** Configuración de API Keys, tokens y otras opciones del sistema.
*   **Visor de Logs Integrado:** Acceso directo a los logs del servidor Flask para facilitar la depuración.
*   **Ejecución de Comandos CLI:** Capacidad de ejecutar comandos de shell directamente desde la interfaz web.
*   **Exportación de Datos:** Exportación de datos de tareas, proyectos y MCPs a formato CSV.
*   **Notificaciones:** Sistema de notificaciones en tiempo real (vía WebSockets) y mensajes flash para eventos importantes.
*   **Autenticación y Autorización:** Sistema de inicio de sesión con Flask-Login y control de acceso basado en roles (RBAC).
*   **Análisis y Estadísticas:** Resumen dinámico del dashboard y gráficos de estadísticas de proyectos y tareas en tiempo real (Chart.js).
*   **Personalización de Interfaz:** Soporte para alternar entre tema oscuro y claro.

## Configuración y Despliegue

Para obtener instrucciones detalladas sobre cómo configurar, instalar dependencias y desplegar el AGP Dashboard Web, por favor, consulta la [Guía de Despliegue y Configuración](docs/DEPLOYMENT.md).

## Uso Local

Una vez configurado, puedes iniciar el dashboard utilizando el script de inicio:

```bash
~/.shortcuts/start_agp_dashboard.sh
```

O, si estás en el entorno virtual del proyecto:

```bash
poetry run python app.py
```

El dashboard estará accesible en `http://0.0.0.0:5000` (o la dirección IP de tu servidor).

## Contribución

Este componente es fundamental para la plataforma AGP. Si deseas contribuir, por favor, consulta la documentación general del proyecto y el `CONTRIBUTING.md` (si existe).
