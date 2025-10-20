from flask import Blueprint

# Defines the Blueprint for version 1 of the API.
# All routes registered with this blueprint will be prefixed with /api/v1.
api_v1_bp = Blueprint(
    'api_v1', 
    __name__,
    url_prefix='/api/v1'
)

# Import the endpoint modules here to register their routes.
# We will add them as we build them.
from . import tasks
