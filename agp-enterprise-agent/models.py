# agp-enterprise-agent/models.py

from enum import Enum
from typing import Optional

from pydantic import BaseModel


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
