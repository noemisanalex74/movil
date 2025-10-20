
from extensions import db
from flask import jsonify
from utils import get_dashboard_stats

from . import api_bp


@api_bp.route("/dashboard/stats")
def api_dashboard_stats():
    """
    Provides a single endpoint to get all stats required for the main dashboard.
    """
    # Models are imported here to avoid circular dependencies if they are moved

    # Note: AgentTask and CustomTool might be deprecated or changed.
    # The get_dashboard_stats function needs to be robust against this.
    # Passing dummy or placeholder models if they don't exist.
    # TODO: Update get_dashboard_stats to not require these models if they are obsolete.
    
    # A better approach would be to refactor get_dashboard_stats to not need these,
    # but for now, we pass them as is.
    stats = get_dashboard_stats(db, None, None)
    return jsonify(stats)
