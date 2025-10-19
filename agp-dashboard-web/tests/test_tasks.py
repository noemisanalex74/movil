import json
import os
import unittest
import uuid
from unittest.mock import patch

from app import create_app


class MockScheduler:
    def init_app(self, app):
        pass

    def start(self):
        pass

    def shutdown(self):
        pass

    @property
    def running(self):
        return False


class TasksBlueprintTestCase(unittest.TestCase):
    def setUp(self):
        """Set up a test client and a temporary tasks file."""
        os.environ["FLASK_TESTING"] = "True"  # Set environment variable for testing
        self.app = create_app()
        self.app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:////" + os.path.join(self.app.instance_path, "main.db")
        self.app.config["TESTING"] = True
        with self.app.app_context():
            from extensions import db
            db.create_all()
        self.app.config["WTF_CSRF_ENABLED"] = False  # Disable CSRF for tests
        self.app.secret_key = "test_secret_key"  # Explicitly set secret key for session
        self.client = self.app.test_client()

        # Create a temporary tasks file for testing
        self.temp_tasks_file = os.path.join(self.app.instance_path, "test_tareas.json")
        self.initial_tasks = [
            {
                "id": str(uuid.uuid4()),
                "descripcion": "Tarea de prueba 1",
                "estado": "pendiente",
                "proyecto": "Proyecto Test",
                "fecha_modificacion": "2023-01-01T12:00:00",
            },
            {
                "id": str(uuid.uuid4()),
                "descripcion": "Tarea de prueba 2",
                "estado": "en_progreso",
                "proyecto": "Proyecto Test",
                "fecha_modificacion": "2023-01-02T12:00:00",
            },
        ]

        # Patch the file path in the tasks blueprint
        self.patcher = patch(
            "blueprints.tasks.TAREAS_FILE", self.temp_tasks_file
        )
        self.patcher.start()



        # Write initial data to the temporary file
        with open(self.temp_tasks_file, "w") as f:
            json.dump(self.initial_tasks, f)

    def tearDown(self):
        """Clean up the temporary tasks file."""
        self.patcher.stop()

        if os.path.exists(self.temp_tasks_file):
            os.remove(self.temp_tasks_file)
        del os.environ["FLASK_TESTING"]  # Unset environment variable

    def test_tasks_manager_page(self):
        """Test if the tasks manager page loads correctly."""
        response = self.client.get("/tasks")
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"Gesti", response.data)

    def test_add_task(self):
        """Test adding a new task."""
        new_task_data = {
            "descripcion": "Nueva tarea desde test",
            "estado": "pendiente",
            "proyecto": "Proyecto Test",
        }
        with self.client.session_transaction() as sess:
            sess["_flashes"] = []  # Clear flashes before request

        response = self.client.post(
            "/task_add", data=new_task_data, follow_redirects=True
        )
        print("Response Data (test_add_task):", response.data)
        print("Response Headers (test_add_task):", response.headers)
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"Tarea a\xc3\xb1adida correctamente.", response.data)

        with open(self.temp_tasks_file, "r") as f:
            tasks = json.load(f)
        self.assertEqual(len(tasks), 3)
        self.assertEqual(tasks[-1]["descripcion"], "Nueva tarea desde test")

    def test_edit_task(self):
        """Test editing an existing task."""
        task_to_edit_id = self.initial_tasks[0]["id"]
        updated_data = {
            "descripcion": "Tarea de prueba 1 (Editada)",
            "estado": "completada",
            "proyecto": "Proyecto Test Editado",
        }
        with self.client.session_transaction() as sess:
            sess["_flashes"] = []  # Clear flashes before request

        response = self.client.post(
            f"/task_edit/{task_to_edit_id}", data=updated_data, follow_redirects=True
        )
        print("Response Data (test_edit_task):", response.data)
        print("Response Headers (test_edit_task):", response.headers)
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"Tarea actualizada correctamente.", response.data)

        with open(self.temp_tasks_file, "r") as f:
            tasks = json.load(f)
        edited_task = next(t for t in tasks if t["id"] == task_to_edit_id)
        self.assertEqual(edited_task["descripcion"], "Tarea de prueba 1 (Editada)")
        self.assertEqual(edited_task["estado"], "completada")

    def test_delete_task(self):
        """Test deleting a task."""
        task_to_delete_id = self.initial_tasks[0]["id"]
        with self.client.session_transaction() as sess:
            sess["_flashes"] = []  # Clear flashes before request

        response = self.client.get(
            f"/task_delete/{task_to_delete_id}", follow_redirects=True
        )
        print("Response Data (test_delete_task):", response.data)
        print("Response Headers (test_delete_task):", response.headers)
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"Tarea eliminada correctamente.", response.data)

        with open(self.temp_tasks_file, "r") as f:
            tasks = json.load(f)
        self.assertEqual(len(tasks), 1)
        self.assertIsNone(next((t for t in tasks if t["id"] == task_to_delete_id), None))

    def test_update_task_status_kanban(self):
        """Test updating a task status via the Kanban API endpoint."""
        task_to_update_id = self.initial_tasks[0]["id"]
        update_data = {"task_id": task_to_update_id, "new_status": "en_progreso"}

        response = self.client.post("/update_task_status", json=update_data)
        self.assertEqual(response.status_code, 200)
        json_response = response.get_json()
        self.assertTrue(json_response["success"])

        with open(self.temp_tasks_file, "r") as f:
            tasks = json.load(f)
        updated_task = next(t for t in tasks if t["id"] == task_to_update_id)
        self.assertEqual(updated_task["estado"], "en_progreso")


if __name__ == "__main__":
    unittest.main()
