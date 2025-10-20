
import os

from extensions import db, migrate
from flask import Flask

# This is a minimal app factory to be used for database migrations only
# It avoids initializing extensions that conflict with the Flask CLI, like SocketIO.

def create_migration_app():
    app = Flask(__name__, instance_relative_config=True)
    
    # Use an absolute path for the database to avoid issues with the CLI's working directory
    db_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "instance")
    os.makedirs(db_dir, exist_ok=True)
    db_path = os.path.join(db_dir, "main.db")
    app.config["SQLALCHEMY_DATABASE_URI"] = f"sqlite:///{db_path}"
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

    # Import all the models so that Alembic can see them

    db.init_app(app)
    migrate.init_app(app, db)

    return app

# The FLASK_APP environment variable should be set to this file
# e.g., export FLASK_APP=migrate.py
app = create_migration_app()
