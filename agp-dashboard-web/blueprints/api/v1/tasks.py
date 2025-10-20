from functools import wraps
import os
import json
from flask import request, jsonify, current_app
from . import api_v1_bp
from models import Setting

def _get_tasks_file_path():
    """Safely gets the path to the tasks JSON file using the app context."""
    return os.path.join(current_app.instance_path, 'tareas.json')

def _load_tasks_from_json():
    """Loads tasks from the JSON file."""
    filepath = _get_tasks_file_path()
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return []

def require_api_key(f):
    """Decorator to protect API endpoints with an API key."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        api_key = request.headers.get('X-API-Key')
        if not api_key:
            return jsonify({"error": "API key is missing"}), 401

        valid_key = Setting.query.filter_by(key='api_key', value=api_key).first()
        if not valid_key:
            return jsonify({"error": "API key is invalid or unauthorized"}), 403
        
        return f(*args, **kwargs)
    return decorated_function

from datetime import datetime

@api_v1_bp.route('/tasks', methods=['GET'])
@require_api_key
def get_tasks():
    """Get a paginated, sorted, and filtered list of tasks."""
    all_tasks = _load_tasks_from_json()

    # Get query parameters
    search_query = request.args.get('search', '').lower()
    status_filter = request.args.get('status', '')
    start_date_str = request.args.get('start_date')
    end_date_str = request.args.get('end_date')
    sort_by = request.args.get('sort_by', 'fecha_modificacion')
    sort_order = request.args.get('sort_order', 'asc') # Default to ascending
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 10, type=int)

    # 1. Filter by search query
    if search_query:
        filtered_tasks = [t for t in all_tasks if search_query in t.get('descripcion', '').lower()]
    else:
        filtered_tasks = all_tasks

    # 2. Filter by status
    if status_filter:
        filtered_tasks = [t for t in filtered_tasks if t.get('estado') == status_filter]

    # 3. Filter by date range
    if start_date_str:
        start_date = datetime.fromisoformat(start_date_str).date()
        filtered_tasks = [t for t in filtered_tasks if t.get('fecha_modificacion') and datetime.fromisoformat(t['fecha_modificacion']).date() >= start_date]
    if end_date_str:
        end_date = datetime.fromisoformat(end_date_str).date()
        filtered_tasks = [t for t in filtered_tasks if t.get('fecha_modificacion') and datetime.fromisoformat(t['fecha_modificacion']).date() <= end_date]

    # 4. Sort
    if sort_by in ['descripcion', 'estado', 'fecha_vencimiento', 'fecha_modificacion']:
        filtered_tasks.sort(
            key=lambda t: (t.get(sort_by) is None, t.get(sort_by, '')),
            reverse=(sort_order == 'desc')
        )

    # 5. Paginate
    total_items = len(filtered_tasks)
    total_pages = (total_items + per_page - 1) // per_page
    start_index = (page - 1) * per_page
    end_index = start_index + per_page
    paginated_tasks = filtered_tasks[start_index:end_index]

    return jsonify({
        'tasks': paginated_tasks,
        'page': page,
        'per_page': per_page,
        'total_pages': total_pages,
        'total_items': total_items,
        'sort_by': sort_by,
        'sort_order': sort_order
    })