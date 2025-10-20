# AGP Enterprise Agent - API Specification

This document defines the API exposed by the `agp-enterprise-agent`. The agent will run a FastAPI server, and this API will only be accessible through the secure tailnet provided by Headscale.

## General Principles

*   **Authentication:** For defense-in-depth, all requests from the dashboard to the agent's API must include a secret bearer token in the `Authorization` header. This pre-shared key will be configured on the agent and in the dashboard's settings for that agent.
*   **Error Handling:** The API will use standard HTTP status codes to indicate success or failure. Response bodies for errors will contain a `detail` key with a descriptive message.
*   **Asynchronous Execution:** Task execution requests are asynchronous. The dashboard sends a task, the agent accepts it and starts it in a background process, and then reports the result back to the dashboard in a separate call.

## Pydantic Models (Data Structures)

These models define the shape of the data sent and received by the API.

```python
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any
from enum import Enum

class TaskStatus(str, Enum):
    """Enum for the status of a task."""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"

class Playbook(BaseModel):
    """Represents an automation playbook."""
    name: str
    content: str  # The actual playbook content, e.g., YAML or a script

class Task(BaseModel):
    """Represents a task to be executed by the agent."""
    task_id: str
    playbook: Playbook

class TaskResult(BaseModel):
    """Represents the result of a task execution to be sent back to the dashboard."""
    task_id: str
    status: TaskStatus
    output: str
    error: Optional[str] = None

```

## Agent API Endpoints (Dashboard -> Agent)

This is the API the agent exposes to the dashboard.

---

### `POST /heartbeat`

*   **Description:** A simple endpoint for the dashboard to check if the agent is alive, reachable, and authenticated.
*   **Request Body:** None
*   **Success Response:**
    *   **Code:** `200 OK`
    *   **Body:** `{"status": "ok"}`
*   **Failure Response:**
    *   `401 Unauthorized`: If the auth token is missing or invalid.

---

### `POST /execute_task`

*   **Description:** The primary endpoint for the dashboard to send a task (e.g., a playbook) to the agent for execution. The agent should start the execution in the background and immediately return a confirmation.
*   **Request Body:** A `Task` object.
*   **Success Response:**
    *   **Code:** `202 Accepted`
    *   **Body:** `{"message": "Task execution started", "task_id": "...", "status": "running"}`
*   **Failure Responses:**
    *   `400 Bad Request`: If the request body is invalid.
    *   `401 Unauthorized`: If the auth token is missing or invalid.
    *   `409 Conflict`: If a task with the same `task_id` is already running.

---

## Dashboard API Endpoints (Agent -> Dashboard)

This is the API the dashboard must expose for the agent to report back. This needs to be defined in the `agp-dashboard-web` project.

---

### `POST /api/v1/agents/report_result`

*   **Description:** Endpoint for the agent to send the final result of a task execution back to the dashboard.
*   **Request Body:** A `TaskResult` object.
*   **Success Response:**
    *   **Code:** `200 OK`
    *   **Body:** `{"message": "Result received"}`
*   **Note:** The dashboard should handle authentication for this endpoint as well, perhaps using a unique token for each agent.

