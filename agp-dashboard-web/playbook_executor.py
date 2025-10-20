import logging
import threading
import uuid

import yaml
from jinja2 import Environment, UndefinedError

log = logging.getLogger(__name__)


class PlaybookExecutor:
    """Orchestrates the execution of a playbook on a target agent."""

    def __init__(self, socketio_instance, connected_agents):
        self.socketio = socketio_instance
        self.connected_agents = connected_agents
        self.jinja_env = Environment()
        # Thread-safe dictionaries to manage async agent responses
        self.pending_responses = {}
        self.response_data = {}

    def run_playbook_from_file(self, playbook_path, agent_id):
        """Loads a playbook from a file and starts the execution thread."""
        log.info(f"Loading playbook from path: {playbook_path}")
        try:
            with open(playbook_path, "r") as f:
                playbook = yaml.safe_load(f)
        except FileNotFoundError:
            log.error(f"Playbook file not found at {playbook_path}")
            # Optionally, emit a failure event to the frontend
            return
        except yaml.YAMLError as e:
            log.error(f"Error parsing playbook YAML at {playbook_path}: {e}")
            return

        # Start execution in a background task managed by SocketIO to not block the main app
        self.socketio.start_background_task(
            target=self._execute_playbook_thread, playbook=playbook, agent_id=agent_id
        )

    def handle_agent_response(self, data):
        """Callback for when an agent sends a response to a task."""
        task_id = data.get("id")  # Following JSON-RPC spec
        if task_id and task_id in self.pending_responses:
            self.response_data[task_id] = data
            self.pending_responses[
                task_id
            ].set()  # Signal that the response is received
        else:
            log.warning(f"Received unhandled or late response for task ID {task_id}")

    def _render_template(self, value, context):
        """Renders a Jinja2 template string with the given context."""
        if not isinstance(value, str):
            return value
        try:
            template = self.jinja_env.from_string(value)
            return template.render(context)
        except UndefinedError as e:
            log.warning(f"Template rendering failed for value '{value}': {e}")
            # Return the raw value if a variable is not found
            return value

    def _evaluate_condition(self, condition_str, context):
        """Evaluates a 'when' condition string."""
        if not condition_str or str(condition_str).lower() == "true":
            return True
        try:
            # Render any variables within the condition first
            rendered_condition = self._render_template(condition_str, context)
            # A simple, safer eval. For more complex logic, a dedicated library is better.
            return eval(str(rendered_condition), {}, context)
        except Exception as e:
            log.error(f"Could not evaluate 'when' condition '{condition_str}': {e}")
            return False

    def _execute_playbook_thread(self, playbook, agent_id):
        playbook_name = playbook.get("name", "Untitled Playbook")
        log.info(
            f"Starting execution of playbook '{playbook_name}' on agent '{agent_id}'."
        )
        self.socketio.emit(
            "playbook_status", {"status": "started", "playbook_name": playbook_name}
        )

        context = playbook.get("vars", {})

        agent_sid = next(
            (
                sid
                for sid, info in self.connected_agents.items()
                if info["id"] == agent_id
            ),
            None,
        )
        if not agent_sid:
            log.error(f"Agent {agent_id} not connected. Aborting playbook.")
            self.socketio.emit(
                "playbook_status",
                {
                    "status": "failed",
                    "playbook_name": playbook_name,
                    "error": f"Agent {agent_id} not connected",
                },
            )
            return

        playbook_success = True
        for task in playbook.get("tasks", []):
            task_name = task.get("name", "Unnamed Task")

            if not self._evaluate_condition(task.get("when"), context):
                log.info(f"Skipping task '{task_name}' due to 'when' condition.")
                self.socketio.emit(
                    "task_status", {"status": "skipped", "task_name": task_name}
                )
                continue

            success, result = self._execute_task_action(task, context, agent_sid)

            if task.get("register"):
                context[task["register"]] = result

            if not success:
                log.error(f"Task '{task_name}' failed. Aborting playbook.")
                playbook_success = False
                break

        final_status = "succeeded" if playbook_success else "failed"
        log.info(f"Playbook '{playbook_name}' finished with status: {final_status}")
        self.socketio.emit(
            "playbook_status", {"status": final_status, "playbook_name": playbook_name}
        )

    def _execute_task_action(self, task, context, agent_sid):
        task_name = task.get("name")
        module = task.get("module")
        args = self._render_template(task.get("args"), context)
        task_id = str(uuid.uuid4())

        log.info(f"Executing task '{task_name}' using module '{module}'.")
        self.socketio.emit("task_status", {"status": "running", "task_name": task_name})

        if module == "debug":
            log.info(f"[DEBUG] {args}")
            result = {"status": "success", "stdout": args, "rc": 0}
            self.socketio.emit(
                "task_status",
                {"status": "success", "task_name": task_name, "result": result},
            )
            return True, result

        if module == "command":
            # Prepare the JSON-RPC request for the agent
            request_payload = {
                "jsonrpc": "2.0",
                "method": "exec_command",
                "params": args.split(),  # Split string into a list for the agent
                "id": task_id,
            }
        else:
            error_msg = f"Module '{module}' is not implemented."
            log.warning(error_msg)
            result = {"status": "failed", "error": error_msg}
            self.socketio.emit(
                "task_status",
                {"status": "failed", "task_name": task_name, "result": result},
            )
            return False, result

        response_event = threading.Event()
        self.pending_responses[task_id] = response_event

        try:
            self.socketio.emit(
                "execute_command", request_payload, room=agent_sid, namespace="/agent"
            )

            if not response_event.wait(timeout=60.0):
                error_msg = "Timeout waiting for agent response."
                log.error(f"Task '{task_name}' timed out.")
                return False, {"status": "failed", "error": error_msg}

            response = self.response_data.pop(task_id, None)
            agent_result = response.get("result", {})
            success = agent_result.get("success", False)

            if success:
                log.info(f"Task '{task_name}' executed successfully.")
                self.socketio.emit(
                    "task_status",
                    {
                        "status": "success",
                        "task_name": task_name,
                        "result": agent_result,
                    },
                )
                return True, agent_result
            else:
                log.error(
                    f"Task '{task_name}' failed on agent. Response: {agent_result}"
                )
                self.socketio.emit(
                    "task_status",
                    {
                        "status": "failed",
                        "task_name": task_name,
                        "result": agent_result,
                    },
                )
                return False, agent_result

        except Exception as e:
            error_msg = f"An unexpected error occurred: {e}"
            log.error(f"Error executing task '{task_name}': {error_msg}")
            return False, {"status": "failed", "error": error_msg}
        finally:
            if task_id in self.pending_responses:
                del self.pending_responses[task_id]
