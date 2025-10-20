import os
import sys

from dashboard_data import (
    get_config_data,
    get_context_memory_data,
    get_custom_tools_data,
    get_tasks_data,
    get_virtual_envs_data,
)
from kivy.app import App
from kivy.properties import StringProperty
from kivy.uix.boxlayout import BoxLayout


class DashboardScreen(BoxLayout):
    general_info = StringProperty("")
    ai_config_info = StringProperty("")
    user_prefs_info = StringProperty("")
    pending_tasks_info = StringProperty("")
    custom_tools_info = StringProperty("")
    virtual_envs_info = StringProperty("")

    def __init__(self, **kwargs):
        super(DashboardScreen, self).__init__(**kwargs)
        self.update_dashboard()

    def update_dashboard(self, *args):
        # --- Información General ---
        self.general_info = (
            f"Directorio de Trabajo: {os.getcwd()}\nSistema Operativo: {sys.platform}"
        )

        # --- Estado de la IA y Configuración ---
        config = get_config_data()
        gemini_api_key_status = (
            "Configurada ✅" if config.get("gemini_api_key") else "No configurada ❌"
        )
        github_token_status = (
            "Configurado ✅" if config.get("github_token") else "No configurado ❌"
        )
        self.ai_config_info = f"API Key de Gemini: {gemini_api_key_status}\nToken de GitHub: {github_token_status}"

        # --- Preferencias del Usuario ---
        context_memory = get_context_memory_data()
        preferencias = context_memory.get("preferencias", {})
        if preferencias:
            self.user_prefs_info = "\n".join(
                [
                    f"- {key.replace('_', ' ').title()}: {value}"
                    for key, value in preferencias.items()
                ]
            )
        else:
            self.user_prefs_info = "No hay preferencias de usuario guardadas."

        # --- Tareas Pendientes ---
        tareas = get_tasks_data()
        pendientes = [t for t in tareas if t.get("estado") == "pendiente"]
        if pendientes:
            self.pending_tasks_info = "\n".join(
                [
                    f"- {i + 1}. {tarea['descripcion']}"
                    for i, tarea in enumerate(pendientes)
                ]
            )
        else:
            self.pending_tasks_info = "No hay tareas pendientes. ¡Bien hecho!"

        # --- Herramientas Personalizadas (MCP) ---
        tools = get_custom_tools_data()
        if tools:
            self.custom_tools_info = "\n".join([f"- {tool}" for tool in tools])
        else:
            self.custom_tools_info = "No hay herramientas personalizadas instaladas."

        # --- Entornos Virtuales ---
        envs = get_virtual_envs_data()
        if envs:
            self.virtual_envs_info = "\n".join([f"- {env}" for env in envs])
        else:
            self.virtual_envs_info = "No hay entornos virtuales creados por AGP CLI."


class AgpDashboardApp(App):
    def build(self):
        return DashboardScreen()


if __name__ == "__main__":
    AgpDashboardApp().run()
