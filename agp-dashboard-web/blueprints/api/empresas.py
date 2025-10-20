
import os

from flask import jsonify
from utils import _load_json

from . import api_bp

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
EMPRESAS_FILE = os.path.join(BASE_DIR, "instance", "empresas.json")

@api_bp.route("/empresas")
def get_empresas():
    empresas = _load_json(EMPRESAS_FILE, [])
    return jsonify({"empresas": empresas})
