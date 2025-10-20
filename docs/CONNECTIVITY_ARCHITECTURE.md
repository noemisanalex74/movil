# Fase 1: Arquitectura de Conectividad

## Objetivo

Definir la arquitectura de conectividad para el sistema de automatización de empresas, permitiendo una comunicación segura y fiable entre el dashboard central y los agentes desplegados en los sistemas de los clientes.

## Decisión de Arquitectura: Zero Trust (ZTNA) con Headscale

Se ha decidido adoptar un **modelo de arquitectura Zero Trust (ZTNA)** como el enfoque fundamental para la conectividad del proyecto. La implementación se basará en **Headscale**, una implementación de código abierto del servidor de coordinación de Tailscale, que utiliza WireGuard para el transporte de datos.

### Justificación

*   **Principio de Mínimo Privilegio:** Headscale nos permite crear una red privada virtual ("tailnet") donde cada nodo (agente, dashboard) es individualmente autenticado. Las reglas de acceso (ACLs) pueden definir qué nodos pueden hablar con cuáles y sobre qué puertos, aplicando el mínimo privilegio.
*   **Seguridad Superior:** El tráfico está cifrado de extremo a extremo con WireGuard. La infraestructura del cliente permanece completamente invisible desde la internet pública. No se exponen puertos.
*   **Control Total:** Al auto-alojar Headscale, tenemos control total sobre el plano de control de la red, sin depender de terceros.
*   **Escalabilidad y Simplicidad:** Añadir un nuevo agente de cliente es tan simple como autenticar un nuevo nodo en la tailnet, lo que lo hace mucho más escalable que gestionar VPNs o túneles SSH individuales.

## Arquitectura Detallada

### Componentes Principales

1.  **Servidor Headscale (Nuestra Infraestructura):**
    *   Será el cerebro de nuestra red privada virtual (tailnet).
    *   Su única función es gestionar la autenticación de los nodos (dashboard y agentes) y coordinar la distribución de las claves de cifrado.
    *   **Importante:** Headscale nunca ve el tráfico de datos. El tráfico viaja directamente de un nodo a otro (peer-to-peer) y siempre está cifrado de extremo a extremo con WireGuard.

2.  **AGP Dashboard (Nuestra Infraestructura):**
    *   Se conectará a la red de Headscale como un nodo más, con su propia IP privada dentro de la tailnet.
    *   Desde el dashboard, gestionaremos los agentes, les enviaremos tareas y visualizaremos los resultados.
    *   Utilizará las IPs privadas de la tailnet para comunicarse directamente con los agentes.

3.  **Agente Empresarial AGP (Infraestructura del Cliente):**
    *   Un programa ligero que se instalará en la máquina del cliente.
    *   Se unirá a nuestra tailnet usando una clave de autenticación que le proporcionaremos.
    *   Expondrá una pequeña API local (usando **FastAPI**).
    *   Esta API **solo será accesible desde el dashboard** a través de la red segura, quedando completamente invisible y aislada de la internet pública.

### Flujo de Comunicación

1.  **Registro del Agente (Enrollment):**
    *   **Paso 1:** Desde el dashboard de AGP, generamos una "clave de registro" de un solo uso para un nuevo cliente/empresa.
    *   **Paso 2:** En la máquina del cliente, ejecutamos el agente por primera vez, pasándole esta clave.
    *   **Paso 3:** El agente usa la clave para autenticarse en nuestro servidor Headscale y se une a la tailnet, recibiendo su IP privada (ej. `100.64.0.2`).
    *   **Paso 4:** Una vez en la red, el agente hace una llamada a la API del dashboard para registrarse formalmente, enviando su información (ej. nombre del host, sistema operativo) y quedando "Activo" en nuestra lista de agentes.

2.  **Comunicación de Tareas (Command & Control):**
    *   **Envío:** El dashboard quiere que un agente ejecute una tarea. Para ello, envía una solicitud directamente a la API del agente a través de su IP privada (ej. `POST http://100.64.0.2:8000/execute_playbook`).
    *   **Ejecución:** El agente recibe la solicitud, la valida y ejecuta la tarea (ej. un playbook de automatización).
    *   **Respuesta:** El agente devuelve el resultado de la tarea haciendo una llamada a la API del dashboard (ej. `POST http://100.64.0.1:5000/task_result`).

## Próximos Pasos

1.  **Definir la API del Agente:** Especificar en detalle los endpoints, modelos de datos (Pydantic) y mecanismos de autenticación para la API que expondrá el `agp-enterprise-agent`.
2.  **Desarrollar el Agente:** Empezar el desarrollo del agente en el directorio `agp-enterprise-agent` basado en la especificación de la API.
3.  **Integrar con el Dashboard:** Modificar el `agp-dashboard-web` para que pueda gestionar los agentes, generar claves y comunicarse con ellos a través de la tailnet.