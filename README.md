# Plataforma de Automatización y Gestión Personal (AGP)

[![Estado del Proyecto](https://img.shields.io/badge/estado-en%20desarrollo%20activo-green.svg)](https://github.com/noemisanalex74/movil)

AGP es un ecosistema de herramientas diseñado para transformar un dispositivo móvil en una estación de trabajo profesional y autónoma, con un fuerte enfoque en la automatización de procesos y la gestión de infraestructura de forma remota.

---

## Visión del Proyecto

La visión principal de AGP es la **Automatización de Empresas**. Buscamos desarrollar un sistema que permita la automatización de tareas y procesos en diferentes empresas de forma remota, utilizando el dispositivo móvil como un centro de operaciones seguro y personalizable.

---

## Componentes Principales

El proyecto está organizado en un monorepo que contiene los siguientes componentes clave:

*   **`agp-dashboard-web/`**: Interfaz web central para la gestión y monitorización de todo el sistema.
*   **`agp-gemini-cli/`**: Herramienta de línea de comandos (CLI) potenciada por IA para interacción, desarrollo y automatización.
*   **`agp-enterprise-agent/`**: Agente ligero y seguro diseñado para ser desplegado en los sistemas remotos de los clientes.
*   **`docs/`**: Documentación centralizada del proyecto.

---

## Hoja de Ruta (Roadmap)

### Plan de Automatización de Empresas

El desarrollo se guía por las siguientes fases:

1.  **Fase 1: Diseño de la Arquitectura de Conectividad:** Investigar y definir la tecnología para conexiones seguras (SSH, ZTNA).
2.  **Fase 2: Desarrollo del Agente de Conectividad:** Crear el agente multiplataforma (Python/Go) para ejecutar tareas remotas.
3.  **Fase 3: Integración con el Dashboard:** Extender el dashboard para gestionar agentes, conexiones y automatizaciones.
4.  **Fase 4: Sistema de Orquestación:** Construir un motor de "playbooks" (YAML/JSON) para definir y programar flujos de trabajo complejos.
5.  **Fase 5: Pruebas Piloto:** Probar y desplegar la solución en un entorno real.

### Módulos Destacados

*   **Laboratorio 3D (3D Lab):** Evolucionar la prueba de concepto actual para convertirla en una herramienta completa de reconstrucción de modelos 3D (`.glb`/`.obj`) a partir de imágenes, integrada con el dashboard.

---

## Pilares Fundamentales

*   **Entorno Portátil:** Optimizar Docker en Termux para tener un entorno de desarrollo completo en el móvil.
*   **Interacción Avanzada:** Evolucionar el CLI con capacidades de audio para una experiencia más natural.
*   **Aprendizaje Autónomo:** Capacitar al CLI para aprender de sus interacciones y optimizar sus propias sugerencias.
*   **Móvil como Centro de Operaciones:** Consolidar todas las capacidades para crear un "super móvil profesional" automatizado.

---

## Inicio Rápido (Desarrollo en Termux)

1.  **Clonar el repositorio (si aún no lo has hecho):**
    ```bash
    git clone https://github.com/noemisanalex74/movil.git
    cd movil
    ```

2.  **Iniciar el Dashboard Web:**
    ```bash
    bash /data/data/com.termux/files/home/.shortcuts/start_agp_dashboard.sh
    ```
    El dashboard estará disponible en `http://localhost:5000`.

---

## Documentación Completa

Para una inmersión profunda en la visión, arquitectura y guías de desarrollo, consulta nuestra documentación.

**[➡️ Ir a la Documentación](docs/index.md)**