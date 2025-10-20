import json
import os
import shlex
import subprocess
from enum import Enum
from typing import List, Optional

import typer
from pydantic import BaseModel, Field

# --- Data Models ---

class CommandModel(BaseModel):
    command: str
    args: List[str] = Field(default_factory=list)
    description: Optional[str] = None

# --- Scope Configuration ---

class Scope(str, Enum):
    user = "user"
    project = "project"

def find_project_root(marker=".git"):
    """Finds the project root by searching upwards for a marker."""
    current_dir = os.getcwd()
    home = os.path.expanduser("~")
    while current_dir != os.path.dirname(home):
        if os.path.exists(os.path.join(current_dir, marker)):
            return current_dir
        parent = os.path.dirname(current_dir)
        if parent == current_dir:
            break
        current_dir = parent
    return home

def get_commands_path(scope: Scope):
    """Gets the path to the commands JSON file for a given scope."""
    if scope == Scope.user:
        config_dir = os.path.expanduser("~/.config/agp-gemini-cli")
        return os.path.join(config_dir, "mcp_commands.v2.json") # New version
    elif scope == Scope.project:
        project_root = find_project_root()
        gemini_dir = os.path.join(project_root, ".gemini")
        return os.path.join(gemini_dir, "mcp_commands.v2.json") # New version
    else:
        raise typer.BadParameter(f"Invalid scope: {scope}")

# --- Typer App ---

mcp_app = typer.Typer(
    name="mcp",
    help="""Gestiona tus herramientas personalizadas (My Custom Python).
    
    Los comandos ahora se guardan en un formato estructurado y más seguro.
    """,
)

# --- Helper Functions ---

def _load_mcp_commands(scope: Scope) -> dict[str, CommandModel]:
    """Loads commands from a specific scope."""
    path = get_commands_path(scope)
    if not os.path.exists(path):
        return {}
    try:
        with open(path, "r") as f:
            data = json.load(f)
            return {name: CommandModel(**cmd_data) for name, cmd_data in data.items()}
    except (json.JSONDecodeError, TypeError):
        typer.secho(f"Warning: Could not parse MCP command file at {path}. It might be corrupted or in an old format.", fg=typer.colors.YELLOW)
        return {}

def _save_mcp_commands(commands: dict[str, CommandModel], scope: Scope):
    """Saves commands to a specific scope."""
    path = get_commands_path(scope)
    dir_name = os.path.dirname(path)
    if not os.path.exists(dir_name):
        os.makedirs(dir_name)
    with open(path, "w") as f:
        # Convert CommandModel objects to dicts for JSON serialization
        data_to_save = {name: cmd.dict() for name, cmd in commands.items()}
        json.dump(data_to_save, f, indent=2)

def _create_command_function(name: str, cmd_model: CommandModel, scope: Scope):
    """Factory to create a typer command function."""
    def command_func(ctx: typer.Context):
        """Dynamically created command."""
        extra_args = ctx.args
        full_command_list = [cmd_model.command] + cmd_model.args + extra_args
        
        typer.echo(f"Executing '{name}' (scope: {scope}): {' '.join(full_command_list)}")
        try:
            # Using list of args is safer (no shell=True)
            subprocess.run(full_command_list, check=True, cwd=find_project_root())
        except FileNotFoundError:
            typer.secho(f"Error: command '{cmd_model.command}' not found.", fg=typer.colors.RED)
        except subprocess.CalledProcessError as e:
            typer.secho(f"Error running command for '{name}': {e}", fg=typer.colors.RED)

    command_func.__name__ = name
    doc = cmd_model.description or f"Runs: {cmd_model.command} {' '.join(cmd_model.args)}"
    command_func.__doc__ = f"(scope: {scope}) {doc}"
    return command_func

def _load_dynamic_commands():
    """Loads all commands from all scopes and registers them, handling precedence."""
    user_commands = _load_mcp_commands(Scope.user)
    project_commands = _load_mcp_commands(Scope.project)

    final_commands = user_commands.copy()
    final_commands.update(project_commands)

    for name, cmd_model in final_commands.items():
        scope = Scope.project if name in project_commands else Scope.user
        help_text = cmd_model.description or f"Runs: {cmd_model.command} ..."
        mcp_app.command(
            name=name,
            context_settings={"allow_extra_args": True, "ignore_unknown_options": True},
            help=help_text,
        )(_create_command_function(name, cmd_model, scope))

# --- MCP Commands ---

@mcp_app.command(name="add")
def mcp_add(
    name: str = typer.Argument(..., help="Nombre del nuevo comando."),
    command_string: str = typer.Argument(..., help="El comando completo a ejecutar, entre comillas si es necesario."),
    scope: Scope = typer.Option(Scope.user, "--scope", "-s", help="El ámbito (scope) del comando."),
    description: str = typer.Option(None, "--desc", "-d", help="Descripción opcional para el comando."),
):
    """Añade un nuevo comando MCP a un ámbito específico."""
    try:
        parts = shlex.split(command_string)
        if not parts:
            raise ValueError("Command string cannot be empty.")
    except ValueError as e:
        typer.secho(f"Error: Invalid command string. {e}", fg=typer.colors.RED)
        raise typer.Abort()

    cmd_model = CommandModel(command=parts[0], args=parts[1:], description=description)
    
    commands = _load_mcp_commands(scope)
    if name in commands:
        typer.secho(f"Warning: El comando '{name}' ya existe en el ámbito '{scope.value}' y será sobrescrito.", fg=typer.colors.YELLOW)
    
    commands[name] = cmd_model
    _save_mcp_commands(commands, scope)
    typer.secho(f"✅ Comando '{name}' añadido/actualizado con éxito en el ámbito '{scope.value}'.", fg=typer.colors.GREEN)

@mcp_app.command(name="remove")
def mcp_remove(
    name: str = typer.Argument(..., help="Nombre del comando a eliminar."),
    scope: Scope = typer.Option(
        None, "--scope", "-s", help="Ámbito específico. Si no se da, se busca en project y luego user."
    ),
):
    """Elimina un comando MCP de un ámbito específico."""
    if scope:
        scopes_to_check = [scope]
    else:
        scopes_to_check = [Scope.project, Scope.user]

    for s in scopes_to_check:
        commands = _load_mcp_commands(s)
        if name in commands:
            del commands[name]
            _save_mcp_commands(commands, s)
            typer.secho(f"✅ Comando '{name}' eliminado con éxito del ámbito '{s.value}'.", fg=typer.colors.GREEN)
            return

    typer.secho(f"Error: El comando '{name}' no se encontró en ningún ámbito.", fg=typer.colors.RED)
    raise typer.Abort()

@mcp_app.command(name="list")
def mcp_list():
    """Lista todos los comandos MCP disponibles, mostrando su ámbito y precedencia."""
    typer.secho("--- Comandos MCP Disponibles ---", fg=typer.colors.BRIGHT_MAGENTA)
    
    user_commands = _load_mcp_commands(Scope.user)
    project_commands = _load_mcp_commands(Scope.project)
    
    if not user_commands and not project_commands:
        typer.echo("No hay comandos MCP configurados.")
        return

    final_commands = user_commands.copy()
    final_commands.update(project_commands)

    if not final_commands:
        typer.echo("No hay comandos MCP configurados.")
        return

    for name in sorted(final_commands.keys()):
        cmd_model = final_commands[name]
        full_cmd_str = ' '.join([cmd_model.command] + cmd_model.args)

        if name in project_commands:
            scope_str = typer.style("project", fg=typer.colors.CYAN, bold=True)
            origin_str = " (sobrescribe user)" if name in user_commands else ""
        else:
            scope_str = typer.style("user", fg=typer.colors.GREEN)
            origin_str = ""
        
        typer.echo(f"- {typer.style(name, bold=True)}: {full_cmd_str}")
        typer.echo(f"  (ámbito: {scope_str}{typer.style(origin_str, fg=typer.colors.YELLOW)})")
        if cmd_model.description:
            typer.echo(f"    {cmd_model.description}")

    typer.secho("----------------------------------", fg=typer.colors.BRIGHT_MAGENTA)

# --- Migration Logic ---

def _migrate_old_format():
    """Migrates commands from the old plain string format to the new structured format."""
    for scope in [Scope.user, Scope.project]:
        old_path = get_commands_path(scope).replace(".v2.json", ".json")
        new_path = get_commands_path(scope)

        if os.path.exists(old_path) and not os.path.exists(new_path):
            typer.secho(f"Migrando archivo de comandos del ámbito '{scope.value}' al nuevo formato...", fg=typer.colors.YELLOW)
            try:
                with open(old_path, 'r') as f:
                    old_commands = json.load(f)
                
                new_commands = {}
                for name, command_string in old_commands.items():
                    parts = shlex.split(command_string)
                    if parts:
                        new_commands[name] = CommandModel(command=parts[0], args=parts[1:])
                
                _save_mcp_commands(new_commands, scope)
                # Optionally, remove the old file after successful migration
                # os.remove(old_path) 
                typer.secho(f"✅ Migración del ámbito '{scope.value}' completada.", fg=typer.colors.GREEN)
            except Exception as e:
                typer.secho(f"Error durante la migración del ámbito '{scope.value}': {e}", fg=typer.colors.RED)

# --- Initialization ---
_migrate_old_format()
_load_dynamic_commands()