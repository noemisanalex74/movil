
from flask import Blueprint, current_app, jsonify, render_template, request
from models import Secret, User, db
from utils import decrypt_value, encrypt_value

vault_bp = Blueprint("vault", __name__)

@vault_bp.route("/vault")
def vault_manager():
    secrets = Secret.query.order_by(Secret.name).all()
    return render_template("vault.html", secrets=secrets)

@vault_bp.route("/api/vault/secrets", methods=["POST"])
def add_secret():
    data = request.get_json()
    name = data.get("name")
    value = data.get("value")

    if not name or not value:
        return jsonify({"error": "Name and value are required"}), 400

    if Secret.query.filter_by(name=name).first():
        return jsonify({"error": "A secret with this name already exists"}), 409

    try:
        encrypted_value = encrypt_value(current_app, value)
        new_secret = Secret(name=name, encrypted_value=encrypted_value)
        db.session.add(new_secret)
        db.session.commit()
        return jsonify({"id": new_secret.id, "name": new_secret.name}), 201
    except Exception as e:
        current_app.logger.error(f"Error encrypting/saving secret: {e}")
        return jsonify({"error": "Could not save secret"}), 500

@vault_bp.route("/api/vault/secrets/<int:secret_id>", methods=["POST"])
def reveal_secret(secret_id):
    data = request.get_json()
    password = data.get("password")
    admin_user = User.query.filter_by(username='admin').first()

    if not admin_user or not admin_user.check_password(password):
        return jsonify({"error": "Invalid password"}), 401

    secret = Secret.query.get_or_404(secret_id)
    try:
        decrypted_value = decrypt_value(current_app, secret.encrypted_value)
        return jsonify({"value": decrypted_value})
    except Exception as e:
        current_app.logger.error(f"Error decrypting secret: {e}")
        return jsonify({"error": "Could not decrypt secret"}), 500

@vault_bp.route("/api/vault/secrets/<int:secret_id>", methods=["DELETE"])
def delete_secret(secret_id):
    secret = Secret.query.get_or_404(secret_id)
    db.session.delete(secret)
    db.session.commit()
    return jsonify({"message": "Secret deleted"}), 200
