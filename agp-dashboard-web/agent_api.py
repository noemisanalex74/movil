import logging
from datetime import datetime, timezone

import jwt
from extensions import db
from flask import current_app, request
from flask_socketio import Namespace, emit, join_room
from models import Agent, AutomationLog

log = logging.getLogger(__name__)


class AgentNamespace(Namespace):
    def __init__(self, namespace, playbook_executor):
        super(AgentNamespace, self).__init__(namespace)
        self.playbook_executor = playbook_executor

    def on_connect(self):
        log.info(f"Agent connected: {request.sid}")
        emit("request_authentication", {"message": "Please authenticate to proceed."})

    def on_disconnect(self):
        if request.sid in current_app.connected_agents:
            agent_info = current_app.connected_agents.pop(request.sid)
            agent_id = agent_info.get("id")
            log.info(
                f"Agent disconnected: {agent_info.get('name', 'Unknown')} (ID: {agent_id}) SID: {request.sid}"
            )

            agent = Agent.query.filter_by(agent_id=agent_id).first()
            if agent:
                agent.status = "offline"
                agent.last_seen = datetime.now(timezone.utc)
                db.session.commit()

                emit(
                    "agent_status_update",
                    {
                        "agent_id": agent_id,
                        "status": "offline",
                        "last_seen": agent.last_seen.strftime("%Y-%m-%d %H:%M:%S UTC"),
                    },
                    broadcast=True,
                    namespace="/agent",
                )
        else:
            log.warning(f"Unauthenticated agent disconnected: {request.sid}")

    def on_authenticate(self, data):
        token = data.get("token")
        if not token:
            log.warning(f"Auth failed (missing token) from SID: {request.sid}")
            return {"status": "error", "message": "Missing authentication token"}

        try:
            unverified_payload = jwt.decode(token, options={"verify_signature": False})
            agent_id = unverified_payload.get("agent_id")

            if not agent_id:
                log.warning(f"Auth failed (agent_id missing) from SID: {request.sid}")
                return {"status": "error", "message": "Agent ID missing in token"}

            agent = Agent.query.filter_by(agent_id=agent_id).first()

            if not agent:
                log.warning(f"Auth failed: Agent ID '{agent_id}' not found.")
                return {"status": "error", "message": "Invalid Agent ID"}

            verified_payload = jwt.decode(token, agent.api_key, algorithms=["HS256"])

            if verified_payload.get("agent_id") != agent_id:
                log.warning(f"Auth failed: Agent ID mismatch for SID: {request.sid}")
                return {"status": "error", "message": "Agent ID mismatch"}

            agent.status = "online"
            agent.last_seen = datetime.now(timezone.utc)
            db.session.commit()

            current_app.connected_agents[request.sid] = {
                "id": agent_id,
                "name": agent.name,
                "sid": request.sid,
                "status": "online",
            }
            join_room(agent_id)
            log.info(
                f"Agent '{agent.name}' authenticated successfully (SID: {request.sid})"
            )

            emit(
                "agent_status_update",
                {
                    "agent_id": agent_id,
                    "status": "online",
                    "last_seen": agent.last_seen.strftime("%Y-%m-%d %H:%M:%S UTC"),
                },
                broadcast=True,
                namespace="/agent",
            )

            return {"status": "success", "message": "Authentication successful"}

        except jwt.ExpiredSignatureError:
            log.warning(f"Auth failed: Token expired for SID: {request.sid}")
            return {"status": "error", "message": "Token has expired"}
        except jwt.InvalidTokenError as e:
            log.warning(f"Auth failed: Invalid token for SID: {request.sid} - {e}")
            return {"status": "error", "message": f"Invalid token: {e}"}
        except Exception as e:
            log.error(f"Unexpected auth error for SID: {request.sid} - {e}")
            return {"status": "error", "message": "Unexpected auth error"}

    def on_server_command(self, data):
        """Handles a command request from the UI and relays it to the agent."""
        agent_id = data.get("agent_id")
        command = data.get("command")
        task_id = data.get("task_id")

        if not all([agent_id, command, task_id]):
            log.warning(f"Invalid server_command received: {data}")
            return

        agent_sid = None
        for sid, agent_info in current_app.connected_agents.items():
            if agent_info.get("id") == agent_id:
                agent_sid = sid
                break

        if agent_sid:
            log.info(
                f"Relaying command '{command}' to agent {agent_id} (SID: {agent_sid})"
            )
            emit(
                "server_command",
                {"method": "exec_command", "params": command, "id": task_id},
                room=agent_sid,
            )
        else:
            log.warning(
                f"Could not find connected agent with ID: {agent_id} to relay command."
            )

    def on_request_health(self, data):
        """Handles a health check request from the UI."""
        agent_id = data.get("agent_id")
        if not agent_id:
            log.warning("Health request received without agent_id")
            return

        agent_sid = None
        for sid, agent_info in current_app.connected_agents.items():
            if agent_info.get("id") == agent_id:
                agent_sid = sid
                break

        if agent_sid:
            log.info(f"Requesting health from agent {agent_id} (SID: {agent_sid})")
            # The agent will respond via the 'on_command_result' event
            emit(
                "server_command",
                {"method": "get_health", "id": f"health_{agent_id}"},
                room=agent_sid,
            )
        else:
            log.warning(
                f"Could not find connected agent with ID: {agent_id} to request health."
            )

    def on_command_result(self, data):
        """Receives the result of a command and passes it to the playbook executor or UI."""
        task_id = data.get("task_id")  # This is the original request ID
        log.info(f"Received result for task/request: {task_id}")

        # Check if this is a health check response
        if task_id and task_id.startswith("health_"):
            agent_id = self.get_agent_id_from_sid(request.sid)
            log.info(f"Received health update from agent {agent_id}")
            emit(
                "health_update",
                {"agent_id": agent_id, "health": data.get("output")},
                broadcast=True,
                namespace="/agent",
            )
            return  # Stop further processing for health checks

        # --- Original command result handling ---
        self.playbook_executor.handle_agent_response(data)

        # We can still log it to the DB here if we want a central command log
        try:
            log_entry = AutomationLog(
                task_id=data.get("task_id"),
                agent_id=self.get_agent_id_from_sid(request.sid),
                type=data.get("type", "command"),
                name=data.get("name", "Unknown Command"),
                status=data.get("status"),
                output=data.get("output"),
            )
            db.session.add(log_entry)
            db.session.commit()
        except Exception as e:
            log.error(f"Error saving command result to DB: {e}")
            db.session.rollback()

    def on_battery_report(self, data):
        """Receives a battery report from an agent and relays it to the UI."""
        agent_id = self.get_agent_id_from_sid(request.sid)
        if agent_id == "Unknown":
            log.warning(
                f"Received battery report from an unknown/unauthenticated agent: {request.sid}"
            )
            return

        log.info(f"Received battery report from agent {agent_id}: {data}")
        # Relay the battery data to all connected browser clients
        # We use the main socketio instance to broadcast to a different namespace if needed,
        # but here we broadcast to the same namespace.
        emit(
            "agent_battery_update",
            {"agent_id": agent_id, "battery": data},
            broadcast=True,
            namespace="/agent",
        )  # Emitting to the same namespace for simplicity

    def get_agent_id_from_sid(self, sid):
        if sid in current_app.connected_agents:
            return current_app.connected_agents[sid].get("id")
        return "Unknown"


def register_agent_namespace(socketio_instance, playbook_executor):
    """Registers the AgentNamespace with the main SocketIO instance."""
    socketio_instance.on_namespace(AgentNamespace("/agent", playbook_executor))
