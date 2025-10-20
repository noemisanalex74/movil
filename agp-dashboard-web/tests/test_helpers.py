import os
import unittest

from utils import _load_json, _save_json


class TestJsonHelpers(unittest.TestCase):
    def setUp(self):
        """Se ejecuta antes de cada test. Prepara un archivo temporal."""
        self.temp_dir = "temp_test_dir"
        os.makedirs(self.temp_dir, exist_ok=True)
        self.test_file_path = os.path.join(self.temp_dir, "test_temp_file.json")

    def tearDown(self):
        """Se ejecuta después de cada test. Limpia el archivo temporal."""
        if os.path.exists(self.test_file_path):
            os.remove(self.test_file_path)
        if os.path.exists(self.temp_dir):
            os.rmdir(self.temp_dir)

    def test_save_and_load_json_success(self):
        """Prueba que se guarda y carga un JSON válido correctamente."""
        test_data = {"key": "value", "number": 123}

        # Guardar los datos
        _save_json(self.test_file_path, test_data)

        # Comprobar que el archivo existe
        self.assertTrue(os.path.exists(self.test_file_path))

        # Cargar los datos y comprobar que son iguales
        loaded_data = _load_json(self.test_file_path)
        self.assertEqual(loaded_data, test_data)

    def test_load_nonexistent_file(self):
        """Prueba que al cargar un archivo inexistente se devuelve el valor por defecto."""
        # Probar con el default implícito (diccionario vacío)
        loaded_data = _load_json("nonexistent_file.json")
        self.assertEqual(loaded_data, {})

        # Probar con un default explícito (lista vacía)
        loaded_data_list = _load_json("nonexistent_file.json", default_value=[])
        self.assertEqual(loaded_data_list, [])

    def test_load_corrupt_json_file(self):
        """Prueba que al cargar un archivo JSON corrupto se devuelve el valor por defecto."""
        # Crear un archivo con contenido inválido
        with open(self.test_file_path, "w") as f:
            f.write('{"key": "value",')  # JSON incompleto y por tanto, corrupto

        # Comprobar que devuelve el valor por defecto
        loaded_data = _load_json(self.test_file_path, default_value={"error": True})
        self.assertEqual(loaded_data, {"error": True})


if __name__ == "__main__":
    unittest.main()
