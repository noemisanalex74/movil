# agp-dashboard-web/blueprints/google_auth.py
from extensions import db
from flask import Blueprint, flash, redirect, request, session, url_for
from google_auth_oauthlib.flow import Flow
from models import Setting

google_auth_bp = Blueprint("google_auth", __name__)

# Este es el "alcance" - le dice a Google qué permisos estamos pidiendo.
# Por ahora, solo necesitamos leer archivos de Drive.
SCOPES = ["https://www.googleapis.com/auth/drive.readonly"]


def get_flow():
    """Crea y configura el objeto Flow de OAuth."""
    client_id = Setting.query.filter_by(key="GOOGLE_CLIENT_ID").first()
    client_secret = Setting.query.filter_by(key="GOOGLE_CLIENT_SECRET").first()

    if not (client_id and client_id.value and client_secret and client_secret.value):
        raise Exception(
            "Client ID o Client Secret de Google no están configurados en los Ajustes."
        )

    client_config = {
        "web": {
            "client_id": client_id.value,
            "client_secret": client_secret.value,
            "auth_uri": "https://accounts.google.com/o/oauth2/auth",
            "token_uri": "https://oauth2.googleapis.com/token",
            "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
            "redirect_uris": [url_for("google_auth.oauth2callback", _external=True)],
        }
    }

    flow = Flow.from_client_config(
        client_config,
        scopes=SCOPES,
        redirect_uri=url_for("google_auth.oauth2callback", _external=True),
    )
    return flow


@google_auth_bp.route("/authorize/google")
def authorize():
    """Inicia el flujo de autorización de OAuth2."""
    try:
        flow = get_flow()
    except Exception as e:
        flash(str(e), "danger")
        return redirect(url_for("threed_lab.lab_dashboard"))

    authorization_url, state = flow.authorization_url(
        access_type="offline", include_granted_scopes="true"
    )
    session["state"] = state
    return redirect(authorization_url)


@google_auth_bp.route("/oauth2callback")
def oauth2callback():
    """La página a la que Google redirige después de la autorización."""
    flow = get_flow()
    flow.fetch_token(authorization_response=request.url)

    credentials = flow.credentials

    # Guardar las credenciales (token) en la base de datos
    cred_setting = Setting.query.filter_by(key="GOOGLE_CREDENTIALS").first()
    if not cred_setting:
        cred_setting = Setting(key="GOOGLE_CREDENTIALS")

    # Convertir credenciales a un formato almacenable (JSON)
    cred_setting.value = credentials.to_json()

    db.session.add(cred_setting)
    db.session.commit()

    flash("¡Conectado con Google Drive con éxito!", "success")
    return redirect(url_for("threed_lab.lab_dashboard"))

