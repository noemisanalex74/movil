#!/bin/bash
# Script para iniciar el Dashboard AGP y abrir el navegador en Termux

PROJECT_DIR="/data/data/com.termux/files/home/agp-dashboard-web"
PORT=5000

echo "🚀 Iniciando el Dashboard AGP..."

# Navegar al directorio del proyecto
cd "$PROJECT_DIR" || {
    echo "Error: No se pudo encontrar el directorio del proyecto en $PROJECT_DIR"
    exit 1
}

# Detener cualquier instancia de Gunicorn que ya esté corriendo para liberar el puerto
echo "- Deteniendo servidores antiguos..."
# Intenta matar procesos Python relacionados con el dashboard
pkill -9 -f "python.*agp-dashboard-web"
# Intenta matar cualquier proceso escuchando en el puerto 5000
fuser -k 5000/tcp 2>/dev/null
sleep 2 # Dar tiempo para que los procesos se detengan

# El directorio de instancia ahora está fuera del proyecto, no se necesita ninguna preparación aquí.

# Activar el entorno virtual y ejecutar Flask en segundo plano
echo "- Iniciando Flask en segundo plano..."
source venv/bin/activate
export FLASK_APP=app.py
export FLASK_DEBUG=1 # Ensure debug mode is active
export PYTHONPATH="$PROJECT_DIR"
# Evitar la creación de archivos .pyc que activan el recargador
export PYTHONDONTWRITEBYTECODE=1
echo "Current working directory before Flask: $(pwd)"
gunicorn -w 4 -b 0.0.0.0:5000 "app:create_app()" --daemon --access-logfile - --error-logfile - --log-level info 

# Esperar un momento para que el servidor se inicie completamente
echo "- Esperando que el servidor se inicie..."
sleep 3

# Abrir la URL en el navegador predeterminado de Termux
echo "- Abriendo el navegador en http://localhost:$PORT"
termux-open "http://localhost:$PORT"

echo "
✅ ¡Listo! El dashboard debería estar abriéndose en tu navegador."
