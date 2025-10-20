
import json
import os
import subprocess
from datetime import datetime

from flask import Blueprint, jsonify, render_template
from utils import _load_json, _save_json

location_bp = Blueprint("location", __name__)

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LOCATIONS_FILE = os.path.join(BASE_DIR, "instance", "locations.json")

def log_location():
    """Gets location from Termux API and saves it to a file."""
    try:
        result = subprocess.run(
            ['termux-location', '-p', 'network', '-r', 'once'],
            capture_output=True, text=True, check=True, timeout=20
        )
        location_data = json.loads(result.stdout)
        
        # Add a timestamp
        location_data['timestamp'] = datetime.now().isoformat()

        locations = _load_json(LOCATIONS_FILE, [])
        locations.append(location_data)
        _save_json(LOCATIONS_FILE, locations)
        print(f"Successfully logged location: {location_data}")

    except Exception as e:
        # Use proper logging in a real app
        print(f"Could not get location: {e}")

@location_bp.route("/locations")
def show_locations():
    """Renders the map view of the location history."""
    return render_template("locations.html")

@location_bp.route("/api/locations")
def api_locations():
    """Returns the location history as JSON."""
    locations = _load_json(LOCATIONS_FILE, [])
    return jsonify(locations)
