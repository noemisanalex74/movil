# Plataforma de Automatización y Gestión Personal (AGP)

[![Estado del Proyecto](https://img.shields.io/badge/estado-en%20desarrollo%20activo-green.svg)](https://github.com/user/repo)

AGP es un ecosistema de herramientas diseñado para la automatización de procesos y la gestión de infraestructura, con un fuerte enfoque en la operación remota y segura desde dispositivos móviles.

---

## Documentación Completa

Toda la información detallada sobre la visión, arquitectura, guías de uso y desarrollo se encuentra en nuestro sitio de documentación.

**[➡️ Ir a la Documentación Completa](docs/index.md)**

---

## Componentes Principales

El proyecto está organizado en un monorepo que contiene los siguientes componentes clave:

*   **[`agp-dashboard-web/`](agp-dashboard-web/):** Interfaz web central para la gestión y monitorización de todo el sistema.
*   **[`agp-gemini-cli/`](agp-gemini-cli/):** Herramienta de línea de comandos para interacción y desarrollo.
*   **[`agp-enterprise-agent/`](agp-enterprise-agent/):** Agente ligero para ser desplegado en sistemas remotos.
*   **[`agp-headscale-poc/`](agp-headscale-poc/):** Prueba de concepto para la red de conectividad segura (ZTNA).

---

## Inicio Rápido (Desarrollo en Termux)

1.  **Clonar el repositorio (si aún no lo has hecho):**
    ```bash
    git clone [URL_DEL_REPOSITORIO]
    cd AGP-Project/
    ```

2.  **Iniciar el Dashboard Web:**
    El método más sencillo para iniciar el entorno de desarrollo principal.
    ```bash
    bash /data/data/com.termux/files/home/.shortcuts/start_agp_dashboard.sh
    ```
    El dashboard estará disponible en `http://localhost:5000`.

---

