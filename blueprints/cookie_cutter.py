#!/usr/bin/env python3
"""
Cookie Cutter Blueprint
Handles cookie cutter STL generation from images
"""

from flask import Blueprint, render_template, request, jsonify, send_file, current_app
from werkzeug.utils import secure_filename
import os
from utils.cookie_logic import generate_cookie_cutter

cookie_bp = Blueprint('cookie', __name__)


def allowed_file(filename):
    """Check if file has an allowed image extension"""
    allowed_extensions = current_app.config.get('ALLOWED_IMAGE_EXTENSIONS', {'png', 'jpg', 'jpeg', 'gif', 'bmp'})
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in allowed_extensions


def validate_params(params):
    """
    Validate cookie cutter parameters against constraints

    Returns:
        tuple: (is_valid, error_message)
    """
    constraints = current_app.config.get('COOKIE_CUTTER_CONSTRAINTS', {})

    for param, (min_val, max_val) in constraints.items():
        value = params.get(param)
        if value is not None and not (min_val <= value <= max_val):
            return False, f"{param} must be between {min_val} and {max_val}"

    return True, None


@cookie_bp.route('/')
def index():
    """Cookie cutter mode UI"""
    return render_template('cookie_cutter.html')


@cookie_bp.route('/api/generate', methods=['POST'])
def generate():
    """
    Generate cookie cutter STL from uploaded image
    
    Expects:
    - image file
    - Optional params: blade_thick, blade_height, base_thick, base_extra, max_dim, no_base
    
    Returns:
    - JSON with download URL or error
    """
    try:
        # Check if image was uploaded
        if 'image' not in request.files:
            return jsonify({'error': 'No image file provided'}), 400
        
        file = request.files['image']
        if file.filename == '':
            return jsonify({'error': 'No file selected'}), 400
        
        if not allowed_file(file.filename):
            return jsonify({'error': 'Invalid file type. Use PNG, JPG, or GIF'}), 400
        
        # Save uploaded file
        filename = secure_filename(file.filename)
        upload_path = os.path.join(current_app.config['UPLOAD_FOLDER'], filename)
        file.save(upload_path)

        # Get default parameters from config
        defaults = current_app.config.get('COOKIE_CUTTER_DEFAULTS', {})

        # Get parameters from request (with defaults from config)
        params = {
            'blade_thick': float(request.form.get('blade_thick', defaults.get('blade_thick', 2.0))),
            'blade_height': float(request.form.get('blade_height', defaults.get('blade_height', 20.0))),
            'base_thick': float(request.form.get('base_thick', defaults.get('base_thick', 3.0))),
            'base_extra': float(request.form.get('base_extra', defaults.get('base_extra', 10.0))),
            'max_dim': float(request.form.get('max_dim', defaults.get('max_dim', 90.0))),
            'no_base': request.form.get('no_base', 'false').lower() == 'true',
            'detail_level': float(request.form.get('detail_level', 0.5))  # 0.0-1.0
        }

        # Validate parameters
        is_valid, error_msg = validate_params(params)
        if not is_valid:
            return jsonify({'error': f'Invalid parameter: {error_msg}'}), 400
        
        # Generate STL
        output_filename = f"cookie_cutter_{os.path.splitext(filename)[0]}.stl"
        output_path = os.path.join(current_app.config['OUTPUT_FOLDER'], output_filename)
        
        mesh = generate_cookie_cutter(upload_path, params)
        mesh.export(output_path)
        
        # Return success with download URL
        return jsonify({
            'success': True,
            'download_url': f'/cookie/download/{output_filename}',
            'stats': {
                'vertices': len(mesh.vertices),
                'faces': len(mesh.faces),
                'is_watertight': mesh.is_watertight
            }
        })
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@cookie_bp.route('/download/<filename>')
def download(filename):
    """Download generated STL file"""
    try:
        filepath = os.path.join(current_app.config['OUTPUT_FOLDER'], secure_filename(filename))
        if os.path.exists(filepath):
            return send_file(filepath, as_attachment=True)
        else:
            return jsonify({'error': 'File not found'}), 404
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@cookie_bp.route('/api/params/default')
def get_default_params():
    """Return default cookie cutter parameters from config"""
    defaults = current_app.config.get('COOKIE_CUTTER_DEFAULTS', {})
    return jsonify({
        **defaults,
        'detail_level': 0.5  # Additional parameter for contour smoothing
    })
