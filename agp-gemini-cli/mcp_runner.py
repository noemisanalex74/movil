import os
import sys

# Añadir el directorio actual al path para poder importar mcp_commands
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from mcp_commands import mcp_app

if __name__ == "__main__":
    mcp_app()
