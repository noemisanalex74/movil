# Bienvenido a la Documentación de AGP - Plataforma de Automatización y Gestión Personal

Este es el portal central de documentación para la **Plataforma de Automatización y Gestión Personal (AGP)**.

## Visión General

El proyecto AGP es un sistema integral diseñado para la automatización de tareas y procesos, con un enfoque particular en la gestión remota de operaciones empresariales y la optimización de la productividad personal en entornos móviles (Termux). La plataforma permite orquestar tareas complejas en múltiples agentes remotos a través de un dashboard centralizado, con un fuerte énfasis en la seguridad, la flexibilidad y la escalabilidad.

## Componentes Principales

El ecosistema AGP consta de tres componentes clave que trabajan en sinergia:

### 1. AGP Dashboard Web (`agp-dashboard-web`)

Es el centro de control y la interfaz gráfica principal del sistema. Construido con **Flask** y **Bootstrap 5**, proporciona una visión completa y capacidades de gestión sobre toda la plataforma, optimizado para una experiencia responsiva en diversos dispositivos.

**Funcionalidades Clave:**
*   **Gestión de Agentes:** Registra, lista y monitoriza el estado de todos los agentes remotos.
*   **Motor de Playbooks:** Permite gestionar y ejecutar Playbooks de automatización (escritos en YAML) sobre los agentes de destino.
*   **Control de Acceso Basado en Roles (RBAC):** Sistema de usuarios con roles (`admin`, `operator`) para proteger acciones críticas y restringir el acceso a funcionalidades sensibles.
*   **Sistema de Notificaciones:** Notificaciones persistentes y en tiempo real (vía WebSockets con Flask-SocketIO) para informar a los usuarios sobre eventos importantes.
*   **Gestión de Tareas y Proyectos:** Herramientas completas para la planificación y seguimiento del trabajo, incluyendo:
    *   Funcionalidad CRUD para tareas y proyectos.
    *   Paginación y búsqueda consistente en tablas de datos.
    *   Registro automático de la fecha de última modificación de tareas.
    *   **Tablero Kanban para Tareas:** Vista visual de tareas con funcionalidad de arrastrar y soltar para cambiar el estado.
*   **Gestión de Herramientas Personalizadas (MCP):** Funcionalidad CRUD para la administración de MCPs.
*   **Gestión de Ajustes (Settings):** Página dedicada para configurar API Keys, Tokens y otras configuraciones.
*   **Visor de Logs Integrado:** Acceso directo a los logs del servidor Flask desde el dashboard.
*   **Ejecución de Comandos del CLI:** Permite ejecutar comandos de shell directamente desde la interfaz web y ver su salida.
*   **Exportación de Datos:** Funcionalidad para exportar tareas, proyectos y MCPs a CSV.
*   **Mejoras de Interfaz de Usuario:**
    *   Menú de navegación lateral (hamburguesa) y mejoras estéticas generales.
    *   Formularios mejorados con clases de Bootstrap y validación básica.
    *   Modales de confirmación de Bootstrap para acciones críticas (ej. eliminación).
    *   Funcionalidad para alternar entre tema oscuro y claro.
*   **Análisis y Estadísticas:**
    *   Resumen general dinámico en la página principal con métricas clave.
    *   Gráficos de estadísticas de proyectos y tareas en tiempo real (usando Chart.js).

### 2. AGP Enterprise Agent (`agp-enterprise-agent`)

Un agente ligero y seguro, escrito en Python con `asyncio`, diseñado para ser desplegado en cualquier sistema cliente (servidor, PC, etc.).

**Funcionalidades Clave:**
*   **Conexión Segura:** Se conecta al dashboard mediante WebSockets seguros (WSS) utilizando autenticación mTLS (autenticación mutua de certificados).
*   **Ejecución de Comandos:** Recibe y ejecuta tareas definidas en los Playbooks, como la ejecución de comandos de shell.
*   **Lista Blanca de Comandos:** Por seguridad, solo puede ejecutar comandos que estén pre-aprobados en su configuración `allowed_commands.json`.
*   **Reporte de Estado:** Mantiene al dashboard informado de su estado (online/offline) a través de un sistema de heartbeats.

### 3. AGP Gemini CLI (`agp-gemini-cli`)

La interfaz de línea de comandos original que sirve como herramienta de desarrollo, gestión y bootstrapping para todo el ecosistema.

**Funcionalidades Clave:**
*   **Integración con Gemini Live API (Streaming):** Permite la generación de texto en streaming, con soporte para entornos como Termux.
*   **Comandos de Herramientas (Tools):** Incluye comandos experimentales como `live-stream-test` y `mcp-server-test` para pruebas y desarrollo.
*   **Investigación de Model Context Protocol (MCP):** Soporte para el protocolo MCP, incluyendo un servidor de ejemplo con FastAPI y fastmcp.

## Arquitectura y Conceptos Clave

*   **Comunicación:** La comunicación Dashboard-Agente se realiza a través de **JSON-RPC** sobre WebSockets, permitiendo un diálogo bidireccional y en tiempo real.
*   **Automatización:** Las tareas se definen en **Playbooks YAML**, inspirados en herramientas como Ansible. Consulta el `PLAYBOOK_SCHEMA.md` para ver la especificación completa.
*   **Seguridad:** La autenticación se basa en un modelo de confianza cero (Zero Trust) con una CA privada y certificados mTLS para cada componente.
*   **Manejo de Errores y Logging:** Implementación de un manejo de errores robusto y un sistema de logging mejorado para facilitar la depuración y el monitoreo.

## Documentación Adicional

Para profundizar en aspectos específicos del proyecto, consulta los siguientes documentos:

*   **[Arquitectura de Conectividad](CONNECTIVITY_ARCHITECTURE.md)**
*   **[Esquema de Playbooks](PLAYBOOK_SCHEMA.md)**
*   **[Visión a Largo Plazo del Proyecto](VISION.md)**
*   **[Guía de Despliegue del Dashboard Web](agp-dashboard-web/DEPLOYMENT.md)**
*   **[README del Frontend del Dashboard Web](agp-dashboard-web/frontend/README.md)**
