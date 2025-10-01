# Guía de Despliegue y Configuración del AGP Dashboard y Agente Enterprise

Este documento detalla los pasos necesarios para configurar y desplegar el AGP Dashboard y el Agente Enterprise en un entorno de producción o pruebas.

## 1. AGP Dashboard (agp-dashboard-web)

El AGP Dashboard es la interfaz central para gestionar agentes, playbooks y automatizaciones.

### 1.1. Requisitos Previos

*   Python 3.8+
*   pip (administrador de paquetes de Python)

### 1.2. Configuración del Entorno

1.  **Navegar al Directorio del Dashboard:**
    ```bash
    cd /data/data/com.termux/files/home/agp-dashboard-web
    ```

2.  **Instalar Dependencias con Poetry:**
    Es altamente recomendable usar Poetry para gestionar las dependencias del proyecto, lo que asegura un entorno virtual aislado y reproducible.
    ```bash
    poetry install
    ```
    Esto creará automáticamente un entorno virtual y instalará todas las dependencias definidas en `pyproject.toml` y `poetry.lock`.

3.  **Variables de Entorno:**
    Configure las siguientes variables de entorno. Es crucial para la seguridad y el funcionamiento.
    *   `SECRET_KEY`: Una cadena aleatoria y segura utilizada por Flask para la seguridad de la sesión. **GENERE UNA CLAVE ÚNICA Y NO LA COMPARTA.**
        ```bash
        export SECRET_KEY="your_super_secret_key_here_replace_me"
        ```
        (Para generar una, puede usar `python -c 'import os; print(os.urandom(24).hex())'`)

4.  **Base de Datos:**
    El dashboard utiliza SQLite por defecto (`instance/site.db`). La base de datos se creará automáticamente al iniciar la aplicación por primera vez si no existe.
    Si desea usar otra base de datos (ej. PostgreSQL, MySQL), deberá:
    *   Instalar el controlador de base de datos correspondiente (`poetry add psycopg2-binary` para PostgreSQL, `poetry add PyMySQL` para MySQL).
    *   Modificar `app.py` para cambiar `SQLALCHEMY_DATABASE_URI`.

### 1.3. Inicio del Dashboard

Para iniciar el dashboard, se recomienda usar el script de inicio proporcionado, especialmente en entornos como Termux, ya que gestiona la activación del entorno virtual:
```bash
~/.shortcuts/start_agp_dashboard.sh
```
Alternativamente, si ya está en el entorno virtual del proyecto (`poetry shell` o `source venv/bin/activate`):
```bash
poetry run python app.py
```
El dashboard estará disponible en `http://0.0.0.0:5000` (o la IP de su servidor).

**Nota de Seguridad:** Para producción, considere usar un servidor WSGI como Gunicorn o uWSGI y un proxy inverso como Nginx para servir la aplicación de forma segura sobre HTTPS.

## 2. Agente Enterprise (agp-enterprise-agent)

El Agente Enterprise se despliega en los sistemas cliente para ejecutar comandos y automatizaciones.

### 2.1. Requisitos Previos

*   Python 3.8+
*   pip (administrador de paquetes de Python)

### 2.2. Configuración del Entorno

1.  **Navegar al Directorio del Agente:**
    ```bash
    cd /data/data/com.termux/files/home/agp-enterprise-agent
    ```

2.  **Crear y Activar un Entorno Virtual (Recomendado):**
    ```bash
    python3 -m venv venv
    source venv/bin/activate
    ```

3.  **Instalar Dependencias:**
    ```bash
    pip install -r requirements.txt
    ```

4.  **Variables de Entorno:**
    Configure las siguientes variables de entorno. Son cruciales para la conexión y autenticación con el dashboard.
    *   `AGP_SERVER_URL`: La URL del dashboard (ej. `wss://your-dashboard.com:5000`). **Debe usar `wss://` para conexiones seguras en producción.**
        ```bash
        export AGP_SERVER_URL="wss://your-dashboard.com:5000"
        ```
    *   `AGP_AGENT_ID`: El ID único del agente. Este ID se genera en el dashboard al registrar un nuevo agente.
        ```bash
        export AGP_AGENT_ID="generated_agent_id_from_dashboard"
        ```
    *   `AGP_AUTH_TOKEN`: El token de autenticación (API Key) generado en el dashboard para este agente.
        ```bash
        export AGP_AUTH_TOKEN="generated_api_key_from_dashboard"
        ```
    *   `AGP_AGENT_BASE_DIR`: El directorio base donde el agente realizará operaciones de archivo (lectura, escritura, eliminación). **Asegúrese de que este directorio tenga los permisos adecuados y esté aislado.**
        ```bash
        export AGP_AGENT_BASE_DIR="/opt/agp-agent-data"
        ```

5.  **Archivo `allowed_commands.json`:**
    Este archivo define qué comandos puede ejecutar el agente y con qué argumentos. **Es una medida de seguridad crítica.** Asegúrese de que este archivo esté configurado con una lista de comandos permitidos y sus patrones de argumentos.
    Ejemplo de `allowed_commands.json`:
    ```json
    [
        {
            "name": "ls",
            "description": "List directory contents",
            "allow_args": true,
            "arg_patterns": [
                "^-.*",
                "^[a-zA-Z0-9_\\-./]+$"
            ]
        },
        {
            "name": "echo",
            "description": "Display a line of text",
            "allow_args": true
        }
    ]
    ```

### 2.3. Inicio del Agente

Una vez configurado, puede iniciar el agente:
```bash
python main.py
```
El agente intentará conectarse al dashboard.

## 3. Configuración de Entorno de Pruebas (Simulación)

Para realizar pruebas piloto, puede simular la infraestructura de una empresa cliente utilizando máquinas virtuales o contenedores Docker.

### 3.1. Usando Docker (Recomendado para Simulación)

Puede crear imágenes Docker para el agente y desplegar múltiples instancias para simular varios agentes en diferentes "empresas".

**Ejemplo de `Dockerfile` para el Agente:**

```dockerfile
# Use an official Python runtime as a parent image
FROM python:3.9-slim-buster

# Set the working directory in the container
WORKDIR /app

# Copy the current directory contents into the container at /app
COPY requirements.txt .
COPY main.py .
COPY config.py .
COPY allowed_commands.json .

# Install any needed packages specified in requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Create the agent base data directory
RUN mkdir -p /opt/agp-agent-data

# Expose the port if the agent were to listen (not directly applicable for Socket.IO client)
# EXPOSE 5000

# Run main.py when the container launches
CMD ["python", "main.py"]
```

**Construir y Ejecutar el Contenedor:**

```bash
# Construir la imagen
docker build -t agp-enterprise-agent .

# Ejecutar un contenedor (reemplace con sus valores)
docker run -d \
  -e AGP_SERVER_URL="wss://your-dashboard.com:5000" \
  -e AGP_AGENT_ID="agent_id_from_dashboard_1" \
  -e AGP_AUTH_TOKEN="api_key_from_dashboard_1" \
  -e AGP_AGENT_BASE_DIR="/opt/agp-agent-data" \
  --name agp-agent-1 \
  agp-enterprise-agent
```
Repita el comando `docker run` con diferentes `AGP_AGENT_ID` y `AGP_AUTH_TOKEN` para simular múltiples agentes.

## 4. Herramientas para Pruebas

### 4.1. Pruebas de Seguridad

*   **OWASP ZAP / Burp Suite:** Para escanear vulnerabilidades web en el dashboard.
*   **Análisis de Código Estático (SAST):** Herramientas como Bandit (para Python) para identificar vulnerabilidades en el código fuente.
*   **Pruebas de Penetración:** Contratar a un experto en seguridad para realizar pruebas de penetración.

### 4.2. Pruebas de Carga

*   **JMeter / Locust:** Para simular un gran número de usuarios o agentes concurrentes y evaluar el rendimiento del dashboard y la capacidad de respuesta del agente.

### 4.3. Monitoreo

*   **Prometheus + Grafana:** Para monitorear métricas del sistema y de la aplicación en tiempo real.
*   **ELK Stack (Elasticsearch, Logstash, Kibana):** Para la agregación y análisis centralizado de logs.

---
**¡Importante!**
Asegúrese de que todas las comunicaciones entre el dashboard y los agentes utilicen **HTTPS/WSS** en entornos de producción.
Revise y audite regularmente el archivo `allowed_commands.json` en cada agente.
