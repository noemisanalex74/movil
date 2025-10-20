import json
import os
import unittest
from datetime import datetime, timedelta
from unittest.mock import patch

from app import create_app
from models import Setting, db
from extensions import scheduler


class APIV1TasksTestCase(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        """Set up the application and test client ONCE for the entire class."""
        cls.app = create_app()
        cls.app.config.update({
            "TESTING": True,
            "SQLALCHEMY_DATABASE_URI": "sqlite:///:memory:",
            "WTF_CSRF_ENABLED": False,
            "SECRET_KEY": "test_secret_key",
            "SCHEDULER_API_ENABLED": False  # Disable scheduler during tests
        })
        cls.client = cls.app.test_client()

        cls.temp_tasks_file = os.path.join(cls.app.instance_path, "test_tareas.json")

        # Mock data with varied dates and statuses
        cls.today = datetime.now()
        cls.initial_tasks = [
            {
                "id": "1", "descripcion": "Tarea completada antigua", "estado": "completada",
                "fecha_modificacion": (cls.today - timedelta(days=10)).isoformat()
            },
            {
                "id": "2", "descripcion": "Tarea pendiente reciente", "estado": "pendiente",
                "fecha_modificacion": (cls.today - timedelta(days=1)).isoformat()
            },
            {
                "id": "3", "descripcion": "Tarea en progreso hoy", "estado": "en_progreso",
                "fecha_modificacion": cls.today.isoformat()
            },
            {
                "id": "4", "descripcion": "Otra tarea pendiente", "estado": "pendiente",
                "fecha_modificacion": (cls.today - timedelta(days=5)).isoformat()
            }
        ]

        # Patch the file path used by the API blueprint
        cls.patcher = patch("blueprints.api.v1.tasks._get_tasks_file_path", return_value=cls.temp_tasks_file)
        cls.patcher.start()

        with open(cls.temp_tasks_file, "w") as f:
            json.dump(cls.initial_tasks, f)

        # Set up in-memory DB and add API Key
        with cls.app.app_context():
            db.create_all()
            cls.api_key = "test-api-key"
            # FIX: Removed invalid 'description' argument
            api_key_setting = Setting(key="api_key", value=cls.api_key)
            db.session.add(api_key_setting)
            db.session.commit()
        
        cls.headers = {"X-API-Key": cls.api_key}

    @classmethod
    def tearDownClass(cls):
        """Tear down the application context and clean up ONCE."""
        cls.patcher.stop()
        if os.path.exists(cls.temp_tasks_file):
            os.remove(cls.temp_tasks_file)
        with cls.app.app_context():
            db.drop_all()
        
        # Shutdown the scheduler if it was started
        if scheduler and scheduler.running:
            scheduler.shutdown(wait=False)

    def test_get_tasks_unauthorized(self):
        """Test that API returns 401 without a key and 403 with a wrong key."""
        response = self.client.get("/api/v1/tasks")
        self.assertEqual(response.status_code, 401)

        response = self.client.get("/api/v1/tasks", headers={"X-API-Key": "wrong-key"})
        self.assertEqual(response.status_code, 403)

    def test_get_all_tasks(self):
        """Test fetching all tasks without filters."""
        response = self.client.get("/api/v1/tasks", headers=self.headers)
        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertEqual(len(data['tasks']), 4)

    def test_filter_by_status(self):
        """Test filtering tasks by status."""
        response = self.client.get("/api/v1/tasks?status=pendiente", headers=self.headers)
        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertEqual(len(data['tasks']), 2)
        self.assertTrue(all(t['estado'] == 'pendiente' for t in data['tasks']))

    def test_filter_by_search_query(self):
        """Test filtering tasks by a search query in the description."""
        response = self.client.get("/api/v1/tasks?search=reciente", headers=self.headers)
        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertEqual(len(data['tasks']), 1)
        self.assertEqual(data['tasks'][0]['id'], '2')

    def test_filter_by_date_range(self):
        """Test filtering tasks by a date range."""
        start_date = (self.today - timedelta(days=6)).strftime('%Y-%m-%d')
        end_date = (self.today - timedelta(days=2)).strftime('%Y-%m-%d')
        response = self.client.get(f"/api/v1/tasks?start_date={start_date}&end_date={end_date}", headers=self.headers)
        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertEqual(len(data['tasks']), 1)
        self.assertEqual(data['tasks'][0]['id'], '4')

    def test_sorting(self):
        """Test sorting tasks by description in ascending order."""
        response = self.client.get("/api/v1/tasks?sort_by=descripcion&sort_order=asc", headers=self.headers)
        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertEqual(len(data['tasks']), 4)
        self.assertEqual(data['tasks'][0]['id'], '4') # "Otra tarea..."
        self.assertEqual(data['tasks'][3]['id'], '2') # "Tarea pendiente..."

    def test_pagination(self):
        """Test pagination of tasks."""
        # Explicitly sort by date ascending for clarity
        response = self.client.get("/api/v1/tasks?sort_by=fecha_modificacion&sort_order=asc&per_page=2&page=2", headers=self.headers)
        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        # With asc sort, page 2 should have the newest items
        self.assertEqual(len(data['tasks']), 2)
        self.assertEqual(data['tasks'][0]['id'], '2')
        self.assertEqual(data['tasks'][1]['id'], '3')
        self.assertEqual(data['total_pages'], 2)
        self.assertEqual(data['page'], 2)

    def test_combined_filters(self):
        """Test a combination of search, status, and sorting."""
        response = self.client.get("/api/v1/tasks?search=tarea&status=pendiente&sort_by=descripcion", headers=self.headers)
        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertEqual(len(data['tasks']), 2)
        self.assertEqual(data['tasks'][0]['id'], '4') # "Otra tarea..."
        self.assertEqual(data['tasks'][1]['id'], '2') # "Tarea pendiente..."

if __name__ == "__main__":
    unittest.main()
