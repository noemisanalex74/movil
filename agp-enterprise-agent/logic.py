# agp-enterprise-agent/logic.py

import asyncio
import json
import os
import subprocess
from typing import Any, Dict, List, Tuple

ALLOWED_COMMANDS_PATH = os.path.join(os.path.dirname(__file__), "allowed_commands.json")

def get_allowed_commands() -> List[str]:
    """Loads the list of allowed commands from the JSON file."""
    try:
        with open(ALLOWED_COMMANDS_PATH, 'r') as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        print("WARN: allowed_commands.json not found or invalid. No commands will be executed.")
        return []

async def execute_command(command_parts: list) -> Tuple[bool, str]:
    """
    Executes a command securely by checking it against a whitelist.
    `command_parts` is a list where the first element is the command
    and subsequent elements are its arguments.
    """
    if not command_parts:
        return False, "No command provided."

    command = command_parts[0]
    args = command_parts[1:]
    allowed_commands = get_allowed_commands()

    if command not in allowed_commands:
        print(f"WARN: Attempt to execute disallowed command: {command}")
        return False, f"Command '{command}' is not allowed."

    try:
        print(f"Executing command: {' '.join(command_parts)}")
        proc = await asyncio.create_subprocess_exec(
            command,
            *args,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        stdout, stderr = await proc.communicate()

        if proc.returncode == 0:
            return True, stdout.decode().strip()
        else:
            return False, stderr.decode().strip()
    except FileNotFoundError:
        return False, f"Command not found: {command}"
    except Exception as e:
        return False, f"Execution failed: {str(e)}"

def get_system_health() -> Dict[str, Any]:
    """Gathers CPU, RAM, and Disk health metrics."""
    health_data: Dict[str, Any] = {}

    # RAM Usage from /proc/meminfo
    try:
        with open('/proc/meminfo', 'r') as f:
            lines = f.readlines()

        mem_total_kb = int(lines[0].split()[1])
        mem_available_kb = int(lines[2].split()[1])
        mem_used_kb = mem_total_kb - mem_available_kb
        ram_percent = (mem_used_kb / mem_total_kb) * 100 if mem_total_kb > 0 else 0
        health_data['ram_percent'] = round(ram_percent, 1)
    except (IOError, IndexError, ValueError) as e:
        health_data['ram_percent'] = -1
        health_data['ram_error'] = str(e)

    # Disk Usage from `df` command
    try:
        result = subprocess.run(['df', '-h', '/'], capture_output=True, text=True, check=True)
        line = result.stdout.strip().splitlines()[-1]
        parts = line.split()
        health_data['disk_percent'] = float(parts[4].replace('%', ''))
    except (subprocess.CalledProcessError, IndexError, ValueError) as e:
        health_data['disk_percent'] = -1
        health_data['disk_error'] = str(e)

    # CPU Load Average from /proc/loadavg
    try:
        with open('/proc/loadavg', 'r') as f:
            load_1m, load_5m, _ = f.read().split()[:3]
        health_data['cpu_load_1m'] = float(load_1m)
        health_data['cpu_load_5m'] = float(load_5m)
    except (IOError, ValueError) as e:
        health_data['cpu_load_1m'] = -1
        health_data['cpu_error'] = str(e)

    return health_data
