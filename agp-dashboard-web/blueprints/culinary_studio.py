
from flask import (Blueprint, current_app, jsonify, render_template, request)
from clients.sd_client import StableDiffusionClient

# Crear un nuevo blueprint
culinary_studio_bp = Blueprint(
    'culinary_studio',
    __name__,
    template_folder='../templates', 
    static_folder='../static'
)

@culinary_studio_bp.route('/culinary_studio')
def studio_page():
    """Muestra la página principal del Estudio Culinario IA."""
    return render_template('culinary_studio.html', title="Estudio Culinario IA")

@culinary_studio_bp.route('/culinary_studio/generate', methods=['POST'])
def generate_image_api():
    """API endpoint que utiliza el cliente de Stable Diffusion para generar una imagen."""
    data = request.get_json()
    prompt = data.get('prompt')
    if not prompt:
        return jsonify({'error': 'El prompt no puede estar vacío.'}), 400

    try:
        client = StableDiffusionClient()
        image_url = client.generate_image(
            prompt=prompt,
            negative_prompt=data.get('negative_prompt', ''),
            steps=data.get('steps', 25),
            sampler=data.get('sampler', 'DPM++ 2M Karras'),
            width=data.get('width', 512),
            height=data.get('height', 512),
            cfg_scale=data.get('cfg_scale', 7)
        )
        
        return jsonify({
            'success': True, 
            'image_url': image_url,
            'message': 'Imagen generada con éxito.'
        })

    except Exception as e:
        error_msg = f"Ocurrió un error durante la generación de la imagen: {e}"
        current_app.logger.error(error_msg)
        return jsonify({'error': error_msg}), 500
