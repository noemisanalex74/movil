import subprocess

from flask import Blueprint, flash, jsonify, redirect, render_template, request, url_for
from flask_login import login_required
from models import Notification, db

notifications_bp = Blueprint(
    "notifications", __name__, template_folder="../templates", url_prefix="/notifications"
)


def create_notification(user_id, message, url=None):
    """Crea y guarda una nueva notificación para un usuario."""
    if not user_id:
        return

    notification = Notification(user_id=user_id, message=message, url=url)
    db.session.add(notification)
    db.session.commit()


@notifications_bp.route("/get_unread")
def get_unread_notifications():
    """Devuelve las notificaciones no leídas del usuario (admin por defecto) en formato JSON."""
    user_id = 1  # Hardcoded to admin user
    unread_notifications = (
        Notification.query.filter_by(user_id=user_id, is_read=False)
        .order_by(Notification.timestamp.desc())
        .all()
    )

    notifs_json = [
        {
            "id": notif.id,
            "message": notif.message,
            "url": notif.url,
            "timestamp": notif.timestamp.isoformat(),
        }
        for notif in unread_notifications
    ]

    return jsonify(notifs_json)


@notifications_bp.route("/mark_read/<int:notification_id>", methods=["POST"])
def mark_as_read(notification_id):
    """Marca una notificación específica como leída."""
    user_id = 1  # Hardcoded to admin user
    notification = Notification.query.get_or_404(notification_id)
    if notification.user_id != user_id:
        return jsonify(success=False, error="Unauthorized"), 403

    notification.is_read = True
    db.session.commit()
    return jsonify(success=True)


@notifications_bp.route("/mark_all_read", methods=["POST"])
def mark_all_as_read():
    """Marca todas las notificaciones del usuario (admin por defecto) como leídas."""
    user_id = 1  # Hardcoded to admin user
    Notification.query.filter_by(user_id=user_id, is_read=False).update(
        {"is_read": True}
    )
    db.session.commit()
    return jsonify(success=True)


@notifications_bp.route("/termux", methods=["GET", "POST"])
@login_required
def termux_notify():
    """
    Muestra un formulario para enviar notificaciones de Termux y maneja el envío.
    """
    if request.method == "POST":
        title = request.form.get("title", "Notificación de AGP-Dashboard")
        content = request.form.get("content")

        if not content:
            flash("El contenido de la notificación no puede estar vacío.", "warning")
            return redirect(url_for("notifications.termux_notify"))

        try:
            # Construir el comando de forma segura
            command = [
                'termux-notification',
                '--title', title,
                '--content', content,
                '--led-color', 'blue',
                '--priority', 'high',
                '--vibrate', '500'
            ]
            
            result = subprocess.run(command, check=True, capture_output=True, text=True)
            flash("Notificación de Termux enviada correctamente.", "success")
        except FileNotFoundError:
            flash("Error: El comando 'termux-notification' no se encontró. Asegúrate de que Termux:API está instalado y configurado.", "danger")
        except subprocess.CalledProcessError as e:
            flash(f"Error al enviar la notificación: {e.stderr}", "danger")
        except Exception as e:
            flash(f"Ocurrió un error inesperado: {str(e)}", "danger")

        return redirect(url_for("notifications.termux_notify"))

    return render_template("termux_notifications.html")
