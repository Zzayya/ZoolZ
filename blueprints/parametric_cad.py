#!/usr/bin/env python3
"""
Parametric CAD Blueprint
OpenSCAD-like programmatic 3D modeling
"""

from flask import Blueprint, render_template, request, jsonify, send_file, current_app
import os
from utils.parametric_cad.cad_operations import (
    create_shape,
    combine_shapes,
    generate_openscad_code,
    render_to_stl,
    reset_shape_registry,
    SHAPE_REGISTRY
)

parametric_bp = Blueprint('parametric', __name__)


@parametric_bp.route('/')
def index():
    """Parametric CAD mode UI"""
    return render_template('parametric_cad.html')


@parametric_bp.route('/api/shapes/available')
def get_available_shapes():
    """Return list of all available shapes with their parameters"""
    shapes = {
        'primitives': {
            'box': {
                'params': ['width', 'height', 'depth', 'wall_thickness'],
                'operations': ['hollow', 'chamfer', 'fillet']
            },
            'cylinder': {
                'params': ['radius', 'height', 'segments'],
                'operations': ['hollow', 'chamfer', 'threads']
            },
            'sphere': {
                'params': ['radius', 'segments'],
                'operations': ['hollow', 'cut_plane']
            },
            'cone': {
                'params': ['bottom_radius', 'top_radius', 'height', 'segments'],
                'operations': ['hollow']
            },
            'torus': {
                'params': ['major_radius', 'minor_radius', 'segments'],
                'operations': []
            },
            'prism': {
                'params': ['sides', 'radius', 'height'],
                'operations': ['hollow', 'chamfer']
            }
        },
        'operations': {
            'boolean': ['union', 'difference', 'intersection'],
            'transforms': ['translate', 'rotate', 'scale', 'mirror'],
            'modifications': [
                'hollow', 'chamfer', 'fillet', 'bevel',
                'male_thread', 'female_thread',
                'brim', 'inverse_brim'
            ]
        }
    }
    return jsonify(shapes)


@parametric_bp.route('/api/shape/create', methods=['POST'])
def create():
    """
    Create a new shape with specified parameters
    
    Expects JSON:
    {
        "shape_type": "box",
        "params": {"width": 10, "height": 20, ...},
        "operations": [...]
    }
    
    Returns:
    - JSON with shape ID and preview data
    """
    try:
        data = request.get_json()
        shape_type = data.get('shape_type')
        params = data.get('params', {})
        operations = data.get('operations', [])
        
        # Create shape using trimesh
        shape = create_shape(shape_type, params, operations)

        # Generate preview (vertices/faces for Three.js)
        preview = shape.to_preview()

        # Generate OpenSCAD code
        openscad_code = generate_openscad_code(shape.id)

        return jsonify({
            'success': True,
            'shape_id': shape.id,
            'preview': preview,
            'openscad_code': openscad_code
        })
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@parametric_bp.route('/api/combine', methods=['POST'])
def combine():
    """
    Combine multiple shapes with boolean operations
    
    Expects JSON:
    {
        "shapes": [shape_id1, shape_id2, ...],
        "operation": "union" | "difference" | "intersection"
    }
    """
    try:
        data = request.get_json()
        shape_ids = data.get('shapes', [])
        operation = data.get('operation', 'union')
        
        result = combine_shapes(shape_ids, operation)

        return jsonify({
            'success': True,
            'result_id': result.id,
            'preview': result.to_preview(),
            'openscad_code': generate_openscad_code(result.id)
        })
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@parametric_bp.route('/api/render', methods=['POST'])
def render():
    """
    Render current design to STL

    Expects JSON:
    {
        "shape_id": "...",
        "filename": "my_design.stl"
    }
    """
    try:
        data = request.get_json()
        shape_id = data.get('shape_id')
        filename = data.get('filename', 'design.stl')

        output_path = os.path.join(current_app.config['OUTPUT_FOLDER'], filename)
        render_to_stl(shape_id, output_path)

        return jsonify({
            'success': True,
            'download_url': f'/parametric/download/{filename}'
        })

    except Exception as e:
        return jsonify({'error': str(e)}), 500


@parametric_bp.route('/download/<filename>')
def download(filename):
    """Download generated STL file"""
    try:
        filepath = os.path.join(current_app.config['OUTPUT_FOLDER'], filename)
        if os.path.exists(filepath):
            return send_file(filepath, as_attachment=True)
        else:
            return jsonify({'error': 'File not found'}), 404
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@parametric_bp.route('/api/openscad/export', methods=['POST'])
def export_openscad():
    """
    Export design as OpenSCAD script

    Expects JSON:
    {
        "shape_id": "..."
    }
    """
    try:
        data = request.get_json()
        shape_id = data.get('shape_id')

        code = generate_openscad_code(shape_id)

        return jsonify({
            'success': True,
            'code': code
        })

    except Exception as e:
        return jsonify({'error': str(e)}), 500


@parametric_bp.route('/api/shapes/reset', methods=['POST'])
def reset_shapes():
    """
    Clear all shapes from the registry (memory cleanup)
    """
    try:
        reset_shape_registry()
        return jsonify({
            'success': True,
            'message': 'All shapes cleared'
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@parametric_bp.route('/api/shapes/list', methods=['GET'])
def list_shapes():
    """
    Get list of all shapes in the registry
    """
    try:
        shapes_list = []
        for shape_id, shape in SHAPE_REGISTRY.items():
            shapes_list.append({
                'id': shape_id,
                'type': shape.shape_type,
                'params': shape.params
            })

        return jsonify({
            'success': True,
            'shapes': shapes_list,
            'count': len(shapes_list)
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500
