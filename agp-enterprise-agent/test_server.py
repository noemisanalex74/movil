# test_server.py
# A simple WebSocket server to test the AGP Enterprise Agent.

import asyncio
import json

import websockets


async def handler(websocket, path):
    """This handler is called for each new connection."""
    agent_id = websocket.request_headers.get("X-Agent-ID", "unknown_agent")
    print(f"\n--- Agent '{agent_id}' connected from {websocket.remote_address} ---")

    try:
        # 1. Send a valid test command to the agent.
        test_command = {
            "jsonrpc": "2.0",
            "method": "exec_command",
            "params": ["ls", "-la"],  # A command from the whitelist
            "id": 1
        }
        print(f"-> Sending command: {json.dumps(test_command)}")
        await websocket.send(json.dumps(test_command))

        # Wait for and print the agent's response.
        response = await websocket.recv()
        print(f"<- Received response: {response}")

        # 2. Send an invalid command to test the security whitelist.
        invalid_command = {
            "jsonrpc": "2.0",
            "method": "exec_command",
            "params": ["rm", "-rf", "/"],  # This should be blocked by the agent
            "id": 2
        }
        print(f"\n-> Sending invalid command: {json.dumps(invalid_command)}")
        await websocket.send(json.dumps(invalid_command))

        # Wait for the "command not allowed" response.
        response = await websocket.recv()
        print(f"<- Received response: {response}")

        print("\n--- Test complete. Keeping connection open to observe agent behavior (e.g., pings). ---")
        # Keep the connection open to see if the agent sends any further messages.
        await asyncio.Future()

    except websockets.exceptions.ConnectionClosed as e:
        print(f"\n--- Connection with agent '{agent_id}' closed: {e} ---")
    except Exception as e:
        print(f"An error occurred: {e}")
    finally:
        print(f"Session with agent '{agent_id}' ended.")

async def main():
    host = "localhost"
    port = 8765
    async with websockets.serve(handler, host, port):
        print(f"Test server listening on ws://{host}:{port}...")
        print("Waiting for an agent to connect.")
        await asyncio.Future()  # Run forever

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nServer stopped by user.")
