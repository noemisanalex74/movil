# This blueprint is being deprecated in favor of the 'enterprise' blueprint.
# It is kept to avoid breaking old imports until a full cleanup is done.
from flask import Blueprint, redirect, url_for

agents_bp = Blueprint("agents", __name__, url_prefix="/agents-fallback")


@agents_bp.route("/")
def list_agents():
    return redirect(url_for("enterprise.list_agents"))

