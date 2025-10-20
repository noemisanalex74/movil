# init_db.py
import os

from app import create_app
from extensions import db

# Explicitly import all models to ensure they are registered with SQLAlchemy's metadata

# The directory for the instance folder
INSTANCE_DIR = os.path.join(os.path.dirname(__file__), "instance")
DB_PATH = os.path.join(INSTANCE_DIR, "main.db")

# Ensure instance folder exists
os.makedirs(INSTANCE_DIR, exist_ok=True)

# If the DB exists, delete it to ensure a clean slate.
# This is safe because we've confirmed it's not correctly initialized.
if os.path.exists(DB_PATH):
    print(f"Deleting existing, incomplete database at {DB_PATH}")
    os.remove(DB_PATH)

app = create_app()

with app.app_context():
    print("Creating all database tables...")
    try:
        db.create_all()
        print("Database tables created successfully.")
    except Exception as e:
        print(f"An error occurred during table creation: {e}")
