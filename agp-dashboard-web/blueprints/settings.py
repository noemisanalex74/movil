from extensions import db
from flask import Blueprint, flash, redirect, render_template, request, url_for
from models import Setting

settings_bp = Blueprint("settings", __name__)

# Define the keys for the settings we want to manage
ALLOWED_SETTINGS = ["GEMINI_API_KEY", "GITHUB_TOKEN", "AIMLAPI_KEY", "FOLDER_OBJETOS3D", "FOLDER_ENTRADA", "FOLDER_SALIDA"]


@settings_bp.route("/settings", methods=["GET", "POST"])
def settings_manager():
    if request.method == "POST":
        for key in ALLOWED_SETTINGS:
            # Only update the value if it was actually submitted in the form
            if key in request.form and request.form[key]:
                setting = Setting.query.filter_by(key=key).first()
                if setting:
                    setting.value = request.form[key]
                else:
                    setting = Setting(key=key, value=request.form[key])
                    db.session.add(setting)

        db.session.commit()
        flash("Ajustes guardados correctamente.", "success")
        return redirect(url_for("settings.settings_manager"))

    # For the GET request, fetch the current settings to display
    current_settings = Setting.query.filter(Setting.key.in_(ALLOWED_SETTINGS)).all()

    # Create a dictionary for easier access in the template
    settings_dict = {setting.key: setting.value for setting in current_settings}

    return render_template(
        "settings.html", settings=settings_dict, allowed_keys=ALLOWED_SETTINGS
    )
