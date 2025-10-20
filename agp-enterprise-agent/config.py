# config.py
import os

# Agent's unique identifier, can be overridden by environment variable
AGENT_ID = os.environ.get("AGP_AGENT_ID", "agent-001-test")

# Dashboard WebSocket URL, can be overridden by environment variable
# The "ws" scheme is for local testing without SSL. For production, it should be "wss".
DASHBOARD_URL = os.environ.get("AGP_DASHBOARD_URL", "ws://localhost:8765")

# Security credentials paths
# In a real scenario, these would be in a secure, non-repo location
CERT_DIR = os.path.join(os.path.dirname(__file__), "certs")
CERT_FILE = os.path.join(CERT_DIR, "agent.pem")
KEY_FILE = os.path.join(CERT_DIR, "agent.key")
CA_FILE = os.path.join(CERT_DIR, "ca.pem")