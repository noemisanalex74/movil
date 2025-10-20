#!/bin/bash

# Colores para la salida
VERDE='\033[0;32m'
AMARILLO='\033[1;33m'
NC='\033[0m' # Sin color

echo -e "${AMARILLO}Iniciando la configuración de AGP Gemini CLI...${NC}"

# Paso 1: Verificar si Termux:API está instalado
echo "[1/5] Verificando la instalación de Termux:API..."
if ! pkg list-installed | grep -q "termux-api"; then
    echo -e "${AMARILLO}Termux:API no está instalado. Instalando ahora...${NC}"
else
    echo -e "${VERDE}Termux:API ya está instalado.${NC}"
fi

# Paso 2: Crear directorio de herramientas personalizadas
echo "[2/5] Creando directorio para herramientas personalizadas (MCP)..."
mkdir -p /data/data/com.termux/files/home/agp-gemini-cli/custom_tools/
echo -e "${VERDE}Directorio 'custom_tools' creado/verificado.${NC}"

# Paso 3: Instalar dependencias de Python
echo "[3/5] Instalando dependencias de Python desde requirements.txt..."
if [ -f "requirements.txt" ]; then
    pip install -r requirements.txt
    echo -e "${VERDE}Dependencias instaladas con éxito.${NC}"
else
    echo -e "${AMARILLO}ADVERTENCIA: No se encontró el archivo requirements.txt. Saltando la instalación de dependencias.${NC}"
fi

# Paso 4: Crear alias para el comando principal (agp)
echo "[4/6] Configurando el alias 'agp'..."
ALIAS_CMD="alias agp='python /data/data/com.termux/files/home/agp-gemini-cli/main.py'"
BASHRC_PATH="/data/data/com.termux/files/home/.bashrc"

if ! grep -qF "$ALIAS_CMD" "$BASHRC_PATH"; then
    echo -e "\n# Alias para AGP Gemini CLI" >> "$BASHRC_PATH"
    echo "$ALIAS_CMD" >> "$BASHRC_PATH"
    echo -e "${VERDE}Alias 'agp' creado en .bashrc.${NC}"
    echo -e "${AMARILLO}Por favor, reinicia tu sesión de Termux o ejecuta 'source ~/.bashrc' para usar el comando 'agp'.${NC}"
else
    echo -e "${VERDE}El alias 'agp' ya está configurado.${NC}"
fi

# Paso 5: Crear ejecutable 'mcp'
echo "[5/6] Creando ejecutable 'mcp'..."
MCP_RUNNER_PATH="/data/data/com.termux/files/home/agp-gemini-cli/mcp_runner.py"
BIN_PATH="/data/data/com.termux/files/usr/bin/mcp"

if [ -f "$BIN_PATH" ]; then
    echo -e "${VERDE}El ejecutable 'mcp' ya existe.${NC}"
else
    ln -s "$MCP_RUNNER_PATH" "$BIN_PATH"
    echo -e "${VERDE}Ejecutable 'mcp' creado en $BIN_PATH.${NC}"
fi

# Paso 6: Guía de permisos
echo -e "[6/6] ${AMARILLO}¡ACCIÓN REQUERIDA! Guía de permisos:${NC}"

echo "Para que todas las funciones del CLI funcionen, necesitas conceder permisos a Termux y Termux:API."
echo "Puedes hacerlo desde los Ajustes de Android > Aplicaciones > Termux (y Termux:API)."
echo "Asegúrate de que los siguientes permisos estén ACTIVADOS:"
echo "  - Contactos"
echo "  - Cámara"
echo "  - Ubicación"
echo "  - Micrófono"
echo "  - Teléfono (para enviar SMS)"

echo -e "\n${VERDE}¡Configuración completada!${NC}"
