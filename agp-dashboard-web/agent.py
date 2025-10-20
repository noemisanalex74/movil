import base64
import fcntl
import json
import os
import platform
import pty
import select
import struct
import termios
import threading
import time

import websocket

# Configuration
SERVER_URL = "ws://127.0.0.1:5000/agent"
AGENT_ID = "agent-001"
AUTH_TOKEN = "your-secret-token"

# Global dictionary to store shell processes and related data
shells = {}


def shell_reader(ws, shell_id):
    """
    Reads output from the shell pty and forwards it to the server.
    This runs in a separate thread for each shell.
    """
    while True:
        try:
            if shell_id not in shells or shells[shell_id]["fd"] is None:
                break

            r, _, _ = select.select([shells[shell_id]["fd"]], [], [], 0.1)
            if r:
                output = os.read(shells[shell_id]["fd"], 1024)
                if output:
                    response = {
                        "type": "shell_output",
                        "shell_id": shell_id,
                        "output": output.decode("utf-8", errors="ignore"),
                    }
                    ws.send(json.dumps(response))
                else:
                    # End of file, process has terminated
                    break
        except Exception as e:
            print(f"Error reading from shell {shell_id}: {e}")
            break

    print(f"Shell reader for {shell_id} terminated.")
    # Clean up the shell session
    if shell_id in shells:
        os.close(shells[shell_id]["fd"])
        shells.pop(shell_id, None)
        # Notify the server that the shell has closed
        try:
            ws.send(json.dumps({"type": "shell_closed", "shell_id": shell_id}))
        except Exception as e:
            print(f"Could not notify server of shell closure for {shell_id}: {e}")


def on_message(ws, message):
    print(f"Received message: {message}")
    try:
        data = json.loads(message)
        msg_type = data.get("type")

        if msg_type == "shell_start":
            shell_id = data.get("shell_id", str(time.time()))

            if shell_id in shells:
                print(f"Shell {shell_id} already exists.")
                return

            pid, fd = pty.fork()
            if pid == 0:
                # Child process
                try:
                    os.execv("/bin/bash", ["/bin/bash"])
                except Exception as e:
                    print(f"Failed to start shell: {e}")
                    os._exit(1)
            else:
                # Parent process
                print(f"Started new shell with PID {pid} and shell_id {shell_id}")
                shells[shell_id] = {"pid": pid, "fd": fd}

                thread = threading.Thread(target=shell_reader, args=(ws, shell_id))
                thread.daemon = True
                thread.start()

                response = {"type": "shell_started", "shell_id": shell_id}
                ws.send(json.dumps(response))

        elif msg_type == "shell_input":
            shell_id = data.get("shell_id")
            input_data = data.get("input")
            if shell_id in shells and input_data:
                os.write(shells[shell_id]["fd"], input_data.encode("utf-8"))

        elif msg_type == "shell_resize":
            shell_id = data.get("shell_id")
            rows = data.get("rows")
            cols = data.get("cols")
            if shell_id in shells and rows and cols:
                fcntl.ioctl(
                    shells[shell_id]["fd"],
                    termios.TIOCSWINSZ,
                    struct.pack("HHHH", rows, cols, 0, 0),
                )

        elif msg_type == "shell_close":
            shell_id = data.get("shell_id")
            if shell_id in shells:
                os.close(shells[shell_id]["fd"])
                shells.pop(shell_id, None)
                print(f"Closed shell {shell_id} by server request.")

        elif msg_type == "list_dir":
            path = data.get("path", ".")
            request_id = data.get("request_id")
            try:
                files = []
                for entry in os.listdir(path):
                    full_path = os.path.join(path, entry)
                    is_dir = os.path.isdir(full_path)
                    files.append({"name": entry, "is_dir": is_dir})
                response = {
                    "type": "list_dir_result",
                    "request_id": request_id,
                    "status": "success",
                    "files": files,
                }
            except Exception as e:
                response = {
                    "type": "list_dir_result",
                    "request_id": request_id,
                    "status": "error",
                    "message": str(e),
                }
            ws.send(json.dumps(response))

        elif msg_type == "read_file":
            file_path = data.get("file_path")
            request_id = data.get("request_id")
            try:
                with open(file_path, "rb") as f:
                    content = base64.b64encode(f.read()).decode("utf-8")
                response = {
                    "type": "read_file_result",
                    "request_id": request_id,
                    "status": "success",
                    "content": content,
                }
            except Exception as e:
                response = {
                    "type": "read_file_result",
                    "request_id": request_id,
                    "status": "error",
                    "message": str(e),
                }
            ws.send(json.dumps(response))

        elif msg_type == "write_file":
            file_path = data.get("file_path")
            content = data.get("content")  # Base64 encoded
            request_id = data.get("request_id")
            try:
                with open(file_path, "wb") as f:
                    f.write(base64.b64decode(content))
                response = {
                    "type": "write_file_result",
                    "request_id": request_id,
                    "status": "success",
                }
            except Exception as e:
                response = {
                    "type": "write_file_result",
                    "request_id": request_id,
                    "status": "error",
                    "message": str(e),
                }
            ws.send(json.dumps(response))

        elif msg_type == "delete_file":
            file_path = data.get("file_path")
            request_id = data.get("request_id")
            try:
                os.remove(file_path)
                response = {
                    "type": "delete_file_result",
                    "request_id": request_id,
                    "status": "success",
                }
            except Exception as e:
                response = {
                    "type": "delete_file_result",
                    "request_id": request_id,
                    "status": "error",
                    "message": str(e),
                }
            ws.send(json.dumps(response))

    except json.JSONDecodeError:
        print("Error decoding JSON from server.")
    except Exception as e:
        print(f"An error occurred: {e}")


def on_error(ws, error):
    print(f"Error: {error}")


def on_close(ws, close_status_code, close_msg):
    print("### closed ###")
    time.sleep(5)
    print("Attempting to reconnect...")
    connect_to_server()


def on_open(ws):
    print("### opened ###")
    auth_data = {
        "type": "auth",
        "agent_id": AGENT_ID,
        "token": AUTH_TOKEN,
        "platform": platform.system(),
        "ip": "127.0.0.1",
    }
    ws.send(json.dumps(auth_data))


def connect_to_server():
    ws = websocket.WebSocketApp(
        SERVER_URL,
        on_open=on_open,
        on_message=on_message,
        on_error=on_error,
        on_close=on_close,
    )
    ws.run_forever()


if __name__ == "__main__":
    connect_to_server()
