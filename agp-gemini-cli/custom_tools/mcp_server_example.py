
import uvicorn
from fastapi import FastAPI
from mcp.server.fastmcp import FastMCP

# Crear una instancia de la aplicación FastAPI
app = FastAPI(
    title="Simple MCP Server",
    description="Un servidor MCP de ejemplo con una herramienta 'echo'.",
    version="0.1.0",
)

# Crear un servidor MCP sin estado
mcp = FastMCP(name="EchoServer", stateless_http=True)

@mcp.tool(description="A simple echo tool")
def echo(message: str) -> str:
    """
    Una herramienta simple que recibe un mensaje y lo devuelve.
    """
    print(f"Mensaje recibido en echo: {message}")
    return f"Echo: {message}"

# Montar el servidor MCP en la aplicación FastAPI
app.mount("/mcp", mcp)

@app.get("/")
def read_root():
    return {"message": "Servidor MCP de ejemplo funcionando. Visite /mcp para interactuar."}

if __name__ == "__main__":
    print("Iniciando servidor en http://127.0.0.1:8000")
    uvicorn.run(app, host="127.0.0.1", port=8000)
