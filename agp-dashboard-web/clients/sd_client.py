
import base64
import os
import uuid
import requests
from flask import current_app, url_for
from models import Setting

class StableDiffusionClient:
    def __init__(self):
        self.api_url = self._get_api_url()

    def _get_api_url(self):
        """Obtiene la URL de la API de la base de datos."""
        url_setting = Setting.query.filter_by(key='STABLE_DIFFUSION_API_URL').first()
        if not url_setting or not url_setting.value:
            current_app.logger.error("La URL de la API de Stable Diffusion no está configurada.")
            return None
        return url_setting.value.rstrip('/')

    def generate_image(self, prompt, negative_prompt="", steps=25, sampler="DPM++ 2M Karras", width=512, height=512, cfg_scale=7):
        """Genera una imagen usando la API de Stable Diffusion y la devuelve como una URL local."""
        if not self.api_url:
            raise ConnectionError("La URL de la API de Stable Diffusion no está configurada.")

        txt2img_url = f"{self.api_url}/sdapi/v1/txt2img"

        payload = {
            "prompt": f"professional food photography, high detail, 8k, {prompt}",
            "negative_prompt": f"bad quality, cartoon, drawing, deformed, ugly, blurry, {negative_prompt}",
            "steps": steps,
            "sampler_name": sampler,
            "width": width,
            "height": height,
            "cfg_scale": cfg_scale,
        }

        current_app.logger.info(f"Enviando petición a Stable Diffusion: {txt2img_url}")
        response = requests.post(url=txt2img_url, json=payload, timeout=120)
        response.raise_for_status()
        r = response.json()

        if 'images' not in r or not r['images']:
            raise ValueError("La respuesta de la API no contiene imágenes.")

        # Decodificar y guardar la imagen
        image_data = base64.b64decode(r['images'][0])
        image_filename = f"{uuid.uuid4()}.png"
        image_path = os.path.join(current_app.static_folder, 'generated_food', image_filename)
        
        with open(image_path, 'wb') as f:
            f.write(image_data)
        current_app.logger.info(f"Imagen guardada en: {image_path}")

        # Devolver la URL local de la imagen
        return url_for('static', filename=f'generated_food/{image_filename}', _external=True)
