from datetime import datetime, timezone
import uuid

from extensions import db
from flask_login import UserMixin
from werkzeug.security import check_password_hash, generate_password_hash

# Define la tabla de asociación para la relación muchos a muchos entre User y Agent
user_agent_association = db.Table(
    "user_agent_association",
    db.Column("user_id", db.Integer, db.ForeignKey("user.id")),
    db.Column("agent_id", db.Integer, db.ForeignKey("agent.id")),
)


class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), index=True, unique=True)
    password_hash = db.Column(db.String(256))

    # Relación con las notificaciones (uno a muchos)
    notifications = db.relationship(
        "Notification",
        back_populates="user",
        lazy="dynamic",
        cascade="all, delete-orphan",
    )

    # Relación con los agentes (muchos a muchos)
    agents = db.relationship(
        "Agent", secondary=user_agent_association, back_populates="users"
    )

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def __repr__(self):
        return f"<User {self.username}>"


class Notification(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    message = db.Column(db.String(256), nullable=False)
    url = db.Column(db.String(256), nullable=True)
    is_read = db.Column(db.Boolean, default=False, nullable=False)
    timestamp = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    user = db.relationship("User", back_populates="notifications")

    def __repr__(self):
        return f"<Notification {self.id} {self.message[:20]}>"


class Agent(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    agent_id = db.Column(db.String(64), unique=True, nullable=False, index=True)
    name = db.Column(db.String(128), nullable=False)
    description = db.Column(db.Text, nullable=True)
    location = db.Column(db.String(128), nullable=True)
    api_key = db.Column(db.String(256), unique=True, nullable=False)
    status = db.Column(db.String(16), default="offline", nullable=False)
    last_seen = db.Column(db.DateTime, nullable=True)
    cpu_load_1m = db.Column(db.Float, nullable=True)
    cpu_load_5m = db.Column(db.Float, nullable=True)
    ram_percent = db.Column(db.Float, nullable=True)
    disk_percent = db.Column(db.Float, nullable=True)
    last_health_report = db.Column(db.DateTime, nullable=True)

    # Relación con los usuarios (muchos a muchos)
    users = db.relationship(
        "User", secondary=user_agent_association, back_populates="agents"
    )

    def __repr__(self):
        return f"<Agent {self.name} ({self.agent_id})>"


class AutomationLog(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    task_id = db.Column(db.String(64), index=True)
    agent_id = db.Column(db.String(64), index=True)
    timestamp = db.Column(
        db.DateTime, default=lambda: datetime.now(timezone.utc), index=True
    )
    type = db.Column(db.String(64))
    name = db.Column(db.String(128))
    status = db.Column(db.String(32))
    output = db.Column(db.Text)

    def __repr__(self):
        return f"<AutomationLog {self.task_id} - {self.name} - {self.status}>"


class Setting(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    key = db.Column(db.String(64), unique=True, nullable=False, index=True)
    value = db.Column(db.String(256), nullable=True)

    def __repr__(self):
        return f"<Setting {self.key}>"


class ThreeDModel(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=True)
    s3_url = db.Column(db.String(255), nullable=False)
    status = db.Column(db.String(20), default='pending') # pending, processing, completed, failed
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f'<ThreeDModel {self.name}>'

class Secret(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False)
    encrypted_value = db.Column(db.LargeBinary, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f'<Secret {self.name}>'

class Project(db.Model):
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name = db.Column(db.String(150), nullable=False)
    description = db.Column(db.Text, nullable=True)
    path = db.Column(db.String(255), nullable=True)
    status = db.Column(db.String(50), nullable=False, default='nuevo')
    last_modified = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    def __repr__(self):
        return f'<Project {self.name}>'

class PromptHistory(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    prompt = db.Column(db.Text, nullable=False)
    negative_prompt = db.Column(db.Text, nullable=True)
    parameters = db.Column(db.JSON, nullable=True)
    generated_image_filename = db.Column(db.String(255), nullable=True)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    user = db.relationship('User', backref=db.backref('prompt_histories', lazy=True))

    def __repr__(self):
        return f'<PromptHistory {self.id}: {self.prompt[:30]}...>'