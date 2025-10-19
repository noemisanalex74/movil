#!/bin/bash

# Script para automatizar la configuración de un nuevo entorno de desarrollo en Termux.
# Este script es idempotente donde sea posible.

echo "Iniciando la configuración del entorno de desarrollo..."

# 1. Actualizar y mejorar los paquetes del sistema
echo "\nActualizando y mejorando los paquetes del sistema..."
pkg update -y && pkg upgrade -y

# 2. Instalar herramientas esenciales
echo "\nInstalando herramientas esenciales (git, python, nodejs-lts, make, clang, pkg-config, libcrypt-dev)..."
pkg install -y git python nodejs-lts make clang pkg-config libcrypt-dev

# 3. Configurar pyenv (si no está ya configurado)
echo "\nConfigurando pyenv para la gestión de versiones de Python..."
if [ ! -d "$HOME/.pyenv" ]; then
    git clone https://github.com/pyenv/pyenv.git ~/.pyenv
    echo 'export PYENV_ROOT="$HOME/.pyenv"' >> ~/.bashrc
    echo 'command -v pyenv >/dev/null || export PATH="$PYENV_ROOT/bin:$PATH"' >> ~/.bashrc
    echo 'eval "$(pyenv init -)"' >> ~/.bashrc
    echo "pyenv instalado. Por favor, reinicia tu sesión de Termux o ejecuta 'source ~/.bashrc'."
else
    echo "pyenv ya está instalado. Actualizando..."
    cd ~/.pyenv && git pull
fi

# 4. Instalar Docker (Termux no soporta Docker directamente, se asume que es para un entorno remoto o WSL)
echo "\nInstalando Docker (nota: Docker no funciona directamente en Termux, esto es para configuración remota)..."
# En Termux, Docker no se puede instalar directamente. Esta sección es un marcador de posición.
# Para entornos remotos, se necesitarían credenciales SSH y comandos específicos.

# 5. Configurar .bashrc (si es necesario)
echo "\nVerificando y configurando .bashrc..."
# Asegurarse de que pyenv esté en el PATH (ya se añadió en el paso 3)
# Puedes añadir otras configuraciones aquí si son necesarias.

echo "\nConfiguración del entorno de desarrollo completada. Por favor, reinicia tu sesión de Termux o ejecuta 'source ~/.bashrc'."
