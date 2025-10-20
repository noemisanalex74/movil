# agp-enterprise-agent/api_server.py

from typing import Any, Dict

import requests  # To send results back to the dashboard
from fastapi import APIRouter, BackgroundTasks, Depends, FastAPI, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from logic import execute_command, get_system_health
from models import Task, TaskResult, TaskStatus

# Placeholder for configuration
# In a real app, this would come from config.py
SECRET_TOKEN = "your_super_secret_token"
DASHBOARD_URL = "http://<IP_DASHBOARD>:5000" # The dashboard's API endpoint
DASHBOARD_API_TOKEN = "dashboard_secret_token"

app = FastAPI(
    title="AGP Enterprise Agent",
    description="API for the AGP Enterprise Agent, accessible via a secure tailnet.",
    version="0.1.0"
)

# Security scheme
auth_scheme = HTTPBearer()

# Dependency to verify the token
async def verify_token(credentials: HTTPAuthorizationCredentials = Depends(auth_scheme)):
    """Dependency to verify the bearer token."""
    if credentials.scheme != "Bearer" or credentials.credentials != SECRET_TOKEN:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or missing token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return credentials

# Create a router for our API endpoints
api_router = APIRouter(dependencies=[Depends(verify_token)])

def report_task_result(result: TaskResult):
    """Sends the task result back to the dashboard."""
    try:
        url = f"{DASHBOARD_URL}/api/v1/agents/report_result"
        headers = {"Authorization": f"Bearer {DASHBOARD_API_TOKEN}"}
        response = requests.post(url, json=result.dict(), headers=headers, timeout=10)
        response.raise_for_status()
        print(f"INFO: Successfully reported result for task {result.task_id} to the dashboard.")
    except requests.RequestException as e:
        print(f"ERROR: Failed to report result for task {result.task_id} to dashboard: {e}")

async def run_task_in_background(task: Task):
    """The actual logic to run the task and report back."""
    print(f"INFO: Executing task {task.task_id} in the background.")
    
    # For now, we assume the playbook content is a simple command string
    # e.g., "ls -la"
    command_parts = task.playbook.content.split()
    success, output = await execute_command(command_parts)
    
    status = TaskStatus.COMPLETED if success else TaskStatus.FAILED
    error_message = output if not success else None
    result_output = output if success else ""

    result = TaskResult(
        task_id=task.task_id,
        status=status,
        output=result_output,
        error=error_message
    )
    
    # Send the report back to the dashboard
    report_task_result(result)
    print(f"INFO: Task {task.task_id} finished with status {status}.")


@api_router.post("/heartbeat", tags=["Status"])
async def heartbeat() -> Dict[str, str]:
    """Check if the agent is alive, reachable, and authenticated."""
    print("INFO: Received heartbeat request.")
    return {"status": "ok"}

@api_router.get("/system_health", tags=["Status"])
async def system_health() -> Dict[str, Any]:
    """Get system health metrics (CPU, RAM, Disk)."""
    print("INFO: Received system health request.")
    return get_system_health()

@api_router.post("/execute_task", status_code=status.HTTP_202_ACCEPTED, tags=["Tasks"])
async def execute_task(task: Task, background_tasks: BackgroundTasks) -> Dict[str, str]:
    """Accepts a task for asynchronous execution."""
    print(f"INFO: Received task {task.task_id} for playbook {task.playbook.name}")
    background_tasks.add_task(run_task_in_background, task)
    return {"message": "Task execution started", "task_id": task.task_id, "status": "running"}


app.include_router(api_router, prefix="/api/v1")

@app.get("/", tags=["Status"])
async def root() -> Dict[str, str]:
    """
    Root endpoint providing basic status.
    """
    return {"message": "AGP Enterprise Agent is running."}