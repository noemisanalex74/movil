# agp-dashboard-web/blueprints/social_media.py
from flask import Blueprint, render_template

social_media_bp = Blueprint("social_media", __name__, url_prefix="/social-media")


@social_media_bp.route("/manager")
def manager():
    return render_template("social_media.html")
