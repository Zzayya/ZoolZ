#!/usr/bin/env python3
"""
Modeling Blueprint
Handles 3D modeling tools: cookie cutter, outline generator, and STL operations
"""

from flask import Blueprint, render_template, request, jsonify, send_file, current_app
from werkzeug.utils import secure_filename
import os
import trimesh
import numpy as np
import logging
import uuid

from programs.Modeling.utils.cookie_logic import (
    generate_cookie_cutter,
    extract_outline_data,
    extract_inner_details,
    generate_cookie_cutter_from_outline,
    generate_detail_stamp_from_outlines
)
from programs.Modeling.utils.stamp_logic import generate_stamp
from programs.Modeling.utils import (
    mesh_utils,
    thicken,
    hollow,
    repair,
    simplify,
    mirror,
    shape_generators,
    scale,
    cut,
    channels,
    bore_hole,
    fidget_generators,
    advanced_operations
)

# Set up logger first
logger = logging.getLogger(__name__)

# Import Celery tasks for background processing
try:
    from tasks import (
        generate_cookie_cutter_task,
        thicken_mesh_task,
        hollow_mesh_task,
        boolean_operation_task
    )
    CELERY_AVAILABLE = True
except ImportError:
    CELERY_AVAILABLE = False
    logger.warning("Celery not available - background tasks disabled")

modeling_bp = Blueprint(
    'modeling',
    __name__,
    template_folder='templates',
    static_folder='static',
    static_url_path='/static'
)

# Safety limits
MAX_FILE_SIZE = 100 * 1024 * 1024  # 100MB
MAX_VERTICES = 10_000_000  # 10 million vertices
MAX_ARRAY_COPIES = 1000  # Maximum array pattern copies


def unique_secure_filename(filename: str) -> str:
    """Return a collision-resistant filename while keeping the original stem."""
    base, ext = os.path.splitext(secure_filename(filename))
    return f"{base}_{uuid.uuid4().hex[:8]}{ext}"


def save_upload(file_obj):
    """
    Save an uploaded file with a unique name to prevent collisions.

    Returns:
        tuple: (absolute_path, stored_filename)
    """
    stored_name = unique_secure_filename(file_obj.filename)
    upload_path = os.path.join(current_app.config['UPLOAD_FOLDER'], stored_name)
    file_obj.save(upload_path)
    return upload_path, stored_name


def convert_numpy_types(obj):
    """
    Recursively convert numpy types to Python native types for JSON serialization.

    Args:
        obj: Object to convert (can be dict, list, numpy type, etc.)

    Returns:
        Object with all numpy types converted to Python natives
    """
    if isinstance(obj, dict):
        return {key: convert_numpy_types(value) for key, value in obj.items()}
    elif isinstance(obj, list):
        return [convert_numpy_types(item) for item in obj]
    elif isinstance(obj, np.integer):
        return int(obj)
    elif isinstance(obj, np.floating):
        return float(obj)
    elif isinstance(obj, np.ndarray):
        return convert_numpy_types(obj.tolist())
    elif isinstance(obj, np.bool_):
        return bool(obj)
    else:
        return obj


def allowed_file(filename):
    """Check if file has an allowed extension (images or STL)"""
    allowed_extensions = current_app.config.get('ALLOWED_IMAGE_EXTENSIONS', {'png', 'jpg', 'jpeg', 'gif', 'bmp', 'stl'})
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


def validate_file_size(file):
    """
    Validate file size doesn't exceed maximum

    Returns:
        tuple: (is_valid, error_message)
    """
    file.seek(0, os.SEEK_END)
    size = file.tell()
    file.seek(0)

    if size > MAX_FILE_SIZE:
        size_mb = size / (1024 * 1024)
        max_mb = MAX_FILE_SIZE / (1024 * 1024)
        return False, f"File too large ({size_mb:.1f}MB). Maximum size is {max_mb:.0f}MB"

    return True, None


def validate_mesh_size(mesh):
    """
    Validate mesh doesn't exceed vertex/face limits

    Returns:
        tuple: (is_valid, error_message)
    """
    if len(mesh.vertices) > MAX_VERTICES:
        return False, f"Mesh too complex ({len(mesh.vertices):,} vertices). Maximum is {MAX_VERTICES:,} vertices"

    return True, None


def validate_shape_params(shape_type, params):
    """
    Validate shape generation parameters

    Returns:
        tuple: (is_valid, error_message)
    """
    # Common constraints for all shapes
    common_constraints = {
        'radius': (0.1, 1000.0),
        'height': (0.1, 1000.0),
        'width': (0.1, 1000.0),
        'length': (0.1, 1000.0),
        'depth': (0.1, 1000.0),
        'thickness': (0.01, 100.0),
        'segments': (3, 360),
        'divisions': (1, 100),
    }

    for param, value in params.items():
        if param in common_constraints:
            min_val, max_val = common_constraints[param]
            if not isinstance(value, (int, float)):
                return False, f"{param} must be a number"
            if not (min_val <= value <= max_val):
                return False, f"{param} must be between {min_val} and {max_val}"

    return True, None


def validate_boolean_compatible(mesh1, mesh2):
    """
    Validate meshes are suitable for boolean operations

    Returns:
        tuple: (is_valid, error_message)
    """
    # Check if meshes are watertight
    if not mesh1.is_watertight:
        return False, "First mesh is not watertight. Repair it first before boolean operations"

    if not mesh2.is_watertight:
        return False, "Second mesh is not watertight. Repair it first before boolean operations"

    # Check if meshes intersect or are close enough
    bounds1 = mesh1.bounds
    bounds2 = mesh2.bounds

    # Simple bounding box intersection check
    if (bounds1[1][0] < bounds2[0][0] or bounds1[0][0] > bounds2[1][0] or
        bounds1[1][1] < bounds2[0][1] or bounds1[0][1] > bounds2[1][1] or
        bounds1[1][2] < bounds2[0][2] or bounds1[0][2] > bounds2[1][2]):
        logger.warning("Meshes do not intersect - boolean operation may produce unexpected results")

    return True, None


@modeling_bp.route('/')
def index():
    """Modeling tool UI with multiple modes"""
    return render_template('modeling.html')


@modeling_bp.route('/api/generate', methods=['POST'])
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
        upload_path, filename = save_upload(file)

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
            'download_url': f'/modeling/download/{output_filename}',
            'stats': {
                'vertices': len(mesh.vertices),
                'faces': len(mesh.faces),
                'is_watertight': mesh.is_watertight
            }
        })
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@modeling_bp.route('/download/<filename>')
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


@modeling_bp.route('/api/params/default')
def get_default_params():
    """Return default cookie cutter parameters from config"""
    defaults = current_app.config.get('COOKIE_CUTTER_DEFAULTS', {})
    return jsonify({
        **defaults,
        'detail_level': 0.5  # Additional parameter for contour smoothing
    })


@modeling_bp.route('/api/extract_outline', methods=['POST'])
def extract_outline():
    """
    Extract outline from image and return as JSON for preview/editing

    Expects:
    - image file
    - Optional: detail_level (0.0-1.0)

    Returns:
    - JSON with outline points array
    """
    try:
        if 'image' not in request.files:
            return jsonify({'error': 'No image file provided'}), 400

        file = request.files['image']
        if file.filename == '':
            return jsonify({'error': 'No file selected'}), 400

        if not allowed_file(file.filename):
            return jsonify({'error': 'Invalid file type. Use PNG, JPG, or GIF'}), 400

        # Save uploaded file
        upload_path, filename = save_upload(file)

        # Get detail level parameter
        detail_level = float(request.form.get('detail_level', 0.5))

        # Extract outline data
        outline_data = extract_outline_data(upload_path, detail_level=detail_level)

        return jsonify({
            'success': True,
            'outline': outline_data,
            'filename': filename
        })

    except Exception as e:
        return jsonify({'error': str(e)}), 500


@modeling_bp.route('/api/extract_details', methods=['POST'])
def extract_details():
    """
    Extract inner detail contours from image for stamp generation

    Expects:
    - image file
    - Optional: precision (0.0-1.0)

    Returns:
    - JSON with array of detail contours
    """
    try:
        if 'image' not in request.files:
            return jsonify({'error': 'No image file provided'}), 400

        file = request.files['image']
        if file.filename == '':
            return jsonify({'error': 'No file selected'}), 400

        if not allowed_file(file.filename):
            return jsonify({'error': 'Invalid file type. Use PNG, JPG, or GIF'}), 400

        # Save uploaded file
        upload_path, filename = save_upload(file)

        # Get precision parameter
        precision = float(request.form.get('precision', 0.5))

        # Extract detail data
        detail_data = extract_inner_details(upload_path, precision=precision)

        return jsonify({
            'success': True,
            'details': detail_data,
            'filename': filename
        })

    except Exception as e:
        return jsonify({'error': str(e)}), 500


@modeling_bp.route('/api/generate_from_outline', methods=['POST'])
def generate_from_outline():
    """
    Generate cookie cutter from pre-extracted outline data (edited by user)

    Expects:
    - JSON body with 'outline_data' and 'params'

    Returns:
    - JSON with download URL
    """
    try:
        data = request.get_json()

        if not data or 'outline_data' not in data:
            return jsonify({'error': 'No outline data provided'}), 400

        outline_data = data['outline_data']
        params = data.get('params', {})

        # Set defaults
        defaults = current_app.config.get('COOKIE_CUTTER_DEFAULTS', {})
        params = {
            'blade_thick': float(params.get('blade_thick', defaults.get('blade_thick', 2.0))),
            'blade_height': float(params.get('blade_height', defaults.get('blade_height', 20.0))),
            'base_thick': float(params.get('base_thick', defaults.get('base_thick', 3.0))),
            'base_extra': float(params.get('base_extra', defaults.get('base_extra', 10.0))),
            'max_dim': float(params.get('max_dim', defaults.get('max_dim', 90.0))),
            'no_base': params.get('no_base', False)
        }

        # Generate STL from outline
        mesh = generate_cookie_cutter_from_outline(outline_data, params)

        # Save output
        output_filename = f"cookie_cutter_edited_{hash(str(outline_data))}.stl"
        output_path = os.path.join(current_app.config['OUTPUT_FOLDER'], output_filename)
        mesh.export(output_path)

        return jsonify({
            'success': True,
            'download_url': f'/modeling/download/{output_filename}',
            'stats': {
                'vertices': len(mesh.vertices),
                'faces': len(mesh.faces),
                'is_watertight': mesh.is_watertight
            }
        })

    except Exception as e:
        return jsonify({'error': str(e)}), 500


@modeling_bp.route('/api/generate_detail_stamp', methods=['POST'])
def generate_detail_stamp():
    """
    Generate detail stamp from inner detail contours

    Expects:
    - JSON body with 'detail_data' and 'params'

    Returns:
    - JSON with download URL
    """
    try:
        data = request.get_json()

        if not data or 'detail_data' not in data:
            return jsonify({'error': 'No detail data provided'}), 400

        detail_data = data['detail_data']
        params = data.get('params', {})

        # Set defaults for stamp
        params = {
            'stamp_depth': float(params.get('stamp_depth', 2.0)),
            'stamp_height': float(params.get('stamp_height', 3.0)),
            'max_dim': float(params.get('max_dim', 90.0))
        }

        # Generate stamp mesh
        mesh = generate_detail_stamp_from_outlines(detail_data, params)

        # Save output
        output_filename = f"detail_stamp_{hash(str(detail_data))}.stl"
        output_path = os.path.join(current_app.config['OUTPUT_FOLDER'], output_filename)
        mesh.export(output_path)

        return jsonify({
            'success': True,
            'download_url': f'/modeling/download/{output_filename}',
            'stats': {
                'vertices': len(mesh.vertices),
                'faces': len(mesh.faces),
                'is_watertight': mesh.is_watertight
            }
        })

    except Exception as e:
        return jsonify({'error': str(e)}), 500


@modeling_bp.route('/api/generate_stamp', methods=['POST'])
def generate_stamp_route():
    """
    Generate professional stamp from outline data
    Supports: positive/negative, sharp/detailed, beveled edges, etc.

    Expects:
    - JSON body with 'outline_data' and 'params'

    Returns:
    - JSON with download URL and stats
    """
    try:
        data = request.get_json()

        if not data or 'outline_data' not in data:
            return jsonify({'error': 'No outline data provided'}), 400

        outline_data = data['outline_data']
        params = data.get('params', {})

        # Set defaults
        stamp_params = {
            'stamp_type': params.get('stamp_type', 'positive'),
            'detail_level': float(params.get('detail_level', 0.5)),
            'base_type': params.get('base_type', 'solid'),
            'base_thickness': float(params.get('base_thickness', 5.0)),
            'detail_height': float(params.get('detail_height', 2.0)),
            'edge_profile': params.get('edge_profile', 'rounded'),
            'bevel_angle': float(params.get('bevel_angle', 30)),
            'bevel_depth': float(params.get('bevel_depth', 2.0)),
            'wall_thickness': float(params.get('wall_thickness', 1.5)),
            'detail_style': params.get('detail_style', 'solid'),
            'max_dimension': float(params.get('max_dimension', 80.0)),
            'handle_height': float(params.get('handle_height', 10.0)),
            'include_handle': params.get('include_handle', True)
        }

        # Generate stamp
        mesh = generate_stamp(outline_data, **stamp_params)

        # Save output
        stamp_type_str = stamp_params['stamp_type']
        output_filename = f"stamp_{stamp_type_str}_{hash(str(outline_data))}.stl"
        output_path = os.path.join(current_app.config['OUTPUT_FOLDER'], output_filename)
        mesh.export(output_path)

        return jsonify({
            'success': True,
            'download_url': f'/modeling/download/{output_filename}',
            'stats': {
                'vertices': len(mesh.vertices),
                'faces': len(mesh.faces),
                'is_watertight': mesh.is_watertight,
                'stamp_type': stamp_type_str,
                'detail_level': stamp_params['detail_level']
            }
        })

    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500


# ============================================================================
# STL OPERATION ROUTES
# ============================================================================

@modeling_bp.route('/api/stl/analyze', methods=['POST'])
def analyze_stl():
    """
    Analyze STL file and return wall detection and mesh information.

    Expects:
    - stl file
    - Optional: max_wall_thickness (default: 2.0mm)

    Returns:
    - Wall information, mesh stats, and issues
    """
    try:
        if 'stl' not in request.files:
            return jsonify({'error': 'No STL file provided'}), 400

        file = request.files['stl']
        if file.filename == '':
            return jsonify({'error': 'No file selected'}), 400

        # Save uploaded STL
        upload_path, filename = save_upload(file)

        # Load mesh
        mesh = mesh_utils.load_stl(upload_path)

        # Get parameters
        max_wall_thickness = float(request.form.get('max_wall_thickness', 2.0))

        # Analyze walls
        wall_info = thicken.get_wall_info(mesh, max_thickness=max_wall_thickness)

        # Analyze mesh issues
        repairer = repair.MeshRepairer(mesh)
        issues = repairer.analyze_issues()

        # Get bounding dimensions
        analyzer = mesh_utils.MeshAnalyzer(mesh)
        dimensions = analyzer.get_bounding_dimensions()

        # Prepare response data and convert all numpy types
        response_data = {
            'success': True,
            'walls': wall_info,
            'issues': issues,
            'dimensions': dimensions,
            'volume': analyzer.calculate_volume(),
            'surface_area': analyzer.calculate_surface_area()
        }

        return jsonify(convert_numpy_types(response_data))

    except Exception as e:
        return jsonify({'error': str(e)}), 500


@modeling_bp.route('/api/stl/thicken', methods=['POST'])
def thicken_stl():
    """
    Thicken walls in STL model.

    Expects:
    - stl file
    - thickness_mm: Amount to thicken (mm)
    - Optional: selected_faces (array of face indices)
    - Optional: auto_detect (bool, default: true)

    Returns:
    - Download URL for thickened STL
    """
    try:
        if 'stl' not in request.files:
            return jsonify({'error': 'No STL file provided'}), 400

        file = request.files['stl']
        if file.filename == '':
            return jsonify({'error': 'No file selected'}), 400

        # Save uploaded STL
        upload_path, filename = save_upload(file)

        # Load mesh
        mesh = mesh_utils.load_stl(upload_path)

        # Get parameters
        thickness_mm = float(request.form.get('thickness_mm', 1.0))
        auto_detect = request.form.get('auto_detect', 'true').lower() == 'true'

        # Get selected faces if provided
        selected_faces = None
        if 'selected_faces' in request.form:
            import json
            selected_faces = json.loads(request.form.get('selected_faces'))

        # Perform thickening
        result = thicken.thicken_selected_walls(
            mesh,
            selected_faces=selected_faces,
            thickness_mm=thickness_mm,
            auto_detect=auto_detect
        )

        # Save result
        output_filename = f"thickened_{os.path.splitext(filename)[0]}.stl"
        output_path = os.path.join(current_app.config['OUTPUT_FOLDER'], output_filename)
        mesh_utils.save_stl(result['mesh'], output_path)

        response_data = {
            'success': True,
            'download_url': f'/modeling/download/{output_filename}',
            'stats': result['stats']
        }

        return jsonify(convert_numpy_types(response_data))

    except Exception as e:
        return jsonify({'error': str(e)}), 500


@modeling_bp.route('/api/stl/hollow', methods=['POST'])
def hollow_stl():
    """
    Hollow out STL model.

    Expects:
    - stl file
    - wall_thickness: Desired wall thickness (mm)
    - Optional: add_drainage (bool, default: true)
    - Optional: drainage_diameter (mm, default: 5.0)

    Returns:
    - Download URL for hollowed STL
    """
    try:
        if 'stl' not in request.files:
            return jsonify({'error': 'No STL file provided'}), 400

        file = request.files['stl']
        if file.filename == '':
            return jsonify({'error': 'No file selected'}), 400

        # Save uploaded STL
        upload_path, filename = save_upload(file)

        # Load mesh
        mesh = mesh_utils.load_stl(upload_path)

        # Get parameters
        wall_thickness = float(request.form.get('wall_thickness', 2.0))
        add_drainage = request.form.get('add_drainage', 'true').lower() == 'true'
        drainage_diameter = float(request.form.get('drainage_diameter', 5.0))

        # Perform hollowing
        result = hollow.hollow_mesh(
            mesh,
            wall_thickness=wall_thickness,
            add_drainage=add_drainage,
            drainage_diameter=drainage_diameter
        )

        # Save result
        output_filename = f"hollow_{os.path.splitext(filename)[0]}.stl"
        output_path = os.path.join(current_app.config['OUTPUT_FOLDER'], output_filename)
        mesh_utils.save_stl(result['mesh'], output_path)

        response_data = {
            'success': True,
            'download_url': f'/modeling/download/{output_filename}',
            'stats': result['stats']
        }

        return jsonify(convert_numpy_types(response_data))

    except Exception as e:
        return jsonify({'error': str(e)}), 500


@modeling_bp.route('/api/stl/repair', methods=['POST'])
def repair_stl():
    """
    Repair STL model (fix normals, holes, non-manifold edges, etc.).

    Expects:
    - stl file
    - Optional: aggressive (bool, default: false)

    Returns:
    - Download URL for repaired STL
    - Repair log with all fixes performed
    """
    try:
        if 'stl' not in request.files:
            return jsonify({'error': 'No STL file provided'}), 400

        file = request.files['stl']
        if file.filename == '':
            return jsonify({'error': 'No file selected'}), 400

        # Save uploaded STL
        upload_path, filename = save_upload(file)

        # Load mesh
        mesh = mesh_utils.load_stl(upload_path)

        # Get parameters
        aggressive = request.form.get('aggressive', 'false').lower() == 'true'

        # Perform repair
        result = repair.repair_mesh(mesh, aggressive=aggressive)

        # Save result
        output_filename = f"repaired_{os.path.splitext(filename)[0]}.stl"
        output_path = os.path.join(current_app.config['OUTPUT_FOLDER'], output_filename)
        mesh_utils.save_stl(result['mesh'], output_path)

        response_data = {
            'success': True,
            'download_url': f'/modeling/download/{output_filename}',
            'repair_log': result['repair_log'],
            'before': result['before'],
            'after': result['after'],
            'improvements': result['improvements']
        }

        return jsonify(convert_numpy_types(response_data))

    except Exception as e:
        return jsonify({'error': str(e)}), 500


@modeling_bp.route('/api/stl/simplify', methods=['POST'])
def simplify_stl():
    """
    Simplify STL model (reduce polygon count).

    Expects:
    - stl file
    - Either target_faces OR reduction_percent
    - Optional: preserve_boundaries (bool, default: true)

    Returns:
    - Download URL for simplified STL
    """
    try:
        if 'stl' not in request.files:
            return jsonify({'error': 'No STL file provided'}), 400

        file = request.files['stl']
        if file.filename == '':
            return jsonify({'error': 'No file selected'}), 400

        # Save uploaded STL
        upload_path, filename = save_upload(file)

        # Load mesh
        mesh = mesh_utils.load_stl(upload_path)

        # Get parameters
        target_faces = None
        reduction_percent = None

        if 'target_faces' in request.form:
            target_faces = int(request.form.get('target_faces'))
        elif 'reduction_percent' in request.form:
            reduction_percent = float(request.form.get('reduction_percent'))
        else:
            return jsonify({'error': 'Must specify target_faces or reduction_percent'}), 400

        preserve_boundaries = request.form.get('preserve_boundaries', 'true').lower() == 'true'

        # Perform simplification
        result = simplify.simplify_mesh(
            mesh,
            target_faces=target_faces,
            reduction_percent=reduction_percent,
            preserve_boundaries=preserve_boundaries
        )

        # Save result
        output_filename = f"simplified_{os.path.splitext(filename)[0]}.stl"
        output_path = os.path.join(current_app.config['OUTPUT_FOLDER'], output_filename)
        mesh_utils.save_stl(result['mesh'], output_path)

        response_data = {
            'success': True,
            'download_url': f'/modeling/download/{output_filename}',
            'stats': result['stats']
        }

        return jsonify(convert_numpy_types(response_data))

    except Exception as e:
        return jsonify({'error': str(e)}), 500


@modeling_bp.route('/api/stl/mirror', methods=['POST'])
def mirror_stl():
    """
    Mirror STL model across axis.

    Expects:
    - stl file
    - axis: 'x', 'y', or 'z'
    - Optional: merge (bool, default: false) - merge original and mirrored

    Returns:
    - Download URL for mirrored STL
    """
    try:
        if 'stl' not in request.files:
            return jsonify({'error': 'No STL file provided'}), 400

        file = request.files['stl']
        if file.filename == '':
            return jsonify({'error': 'No file selected'}), 400

        # Save uploaded STL
        upload_path, filename = save_upload(file)

        # Load mesh
        mesh = mesh_utils.load_stl(upload_path)

        # Get parameters
        axis = request.form.get('axis', 'x').lower()
        merge = request.form.get('merge', 'false').lower() == 'true'

        if axis not in ['x', 'y', 'z']:
            return jsonify({'error': 'Invalid axis. Use x, y, or z'}), 400

        # Perform mirroring
        result = mirror.mirror_mesh(mesh, axis=axis, merge=merge)

        # Save result
        output_filename = f"mirrored_{axis}_{os.path.splitext(filename)[0]}.stl"
        output_path = os.path.join(current_app.config['OUTPUT_FOLDER'], output_filename)
        mesh_utils.save_stl(result['mesh'], output_path)

        response_data = {
            'success': True,
            'download_url': f'/modeling/download/{output_filename}',
            'stats': result['stats']
        }

        return jsonify(convert_numpy_types(response_data))

    except Exception as e:
        return jsonify({'error': str(e)}), 500

# ============================================================================
# ADVANCED STL TOOLS - Boolean, Split, Array
# ============================================================================

@modeling_bp.route('/api/stl/boolean', methods=['POST'])
def boolean_operation():
    """
    Perform boolean operations on two STL meshes (Union, Subtract, Intersect)
    """
    try:
        # Get files and operation type
        if 'mesh1' not in request.files or 'mesh2' not in request.files:
            return jsonify({'error': 'Two STL files required'}), 400

        operation = request.form.get('operation', 'union')  # union, difference, intersection

        # Load both meshes
        mesh1_file = request.files['mesh1']
        mesh2_file = request.files['mesh2']

        # Validate file sizes
        is_valid, error_msg = validate_file_size(mesh1_file)
        if not is_valid:
            return jsonify({'error': f'First file: {error_msg}'}), 400

        is_valid, error_msg = validate_file_size(mesh2_file)
        if not is_valid:
            return jsonify({'error': f'Second file: {error_msg}'}), 400

        # Read meshes
        mesh1 = trimesh.load(mesh1_file, file_type='stl')
        mesh2 = trimesh.load(mesh2_file, file_type='stl')

        # Validate mesh sizes
        is_valid, error_msg = validate_mesh_size(mesh1)
        if not is_valid:
            return jsonify({'error': f'First mesh: {error_msg}'}), 400

        is_valid, error_msg = validate_mesh_size(mesh2)
        if not is_valid:
            return jsonify({'error': f'Second mesh: {error_msg}'}), 400

        # Validate meshes are suitable for boolean operations
        is_valid, error_msg = validate_boolean_compatible(mesh1, mesh2)
        if not is_valid:
            return jsonify({'error': error_msg}), 400

        # Perform boolean operation
        if operation == 'union':
            result_mesh = mesh1.union(mesh2)
        elif operation == 'difference' or operation == 'subtract':
            result_mesh = mesh1.difference(mesh2)
        elif operation == 'intersection' or operation == 'intersect':
            result_mesh = mesh1.intersection(mesh2)
        else:
            return jsonify({'error': f'Unknown operation: {operation}'}), 400

        # Validate result mesh size
        is_valid, error_msg = validate_mesh_size(result_mesh)
        if not is_valid:
            return jsonify({'error': f'Result mesh: {error_msg}'}), 400

        # Save result to outputs (avoid polluting uploads and reduce collisions)
        output_filename = f"boolean_{operation}_{uuid.uuid4().hex[:8]}.stl"
        output_path = os.path.join(current_app.config['OUTPUT_FOLDER'], output_filename)
        result_mesh.export(output_path)

        # Calculate stats
        stats = {
            'vertices': len(result_mesh.vertices),
            'faces': len(result_mesh.faces),
            'is_watertight': result_mesh.is_watertight,
            'volume': float(result_mesh.volume) if result_mesh.is_watertight else None,
            'operation': operation
        }

        response_data = {
            'success': True,
            'download_url': f'/modeling/download/{os.path.basename(output_path)}',
            'stats': stats
        }

        logger.info(f"Boolean {operation} completed: {len(result_mesh.vertices)} vertices")
        return jsonify(convert_numpy_types(response_data))

    except Exception as e:
        logger.error(f"Error in boolean operation: {str(e)}")
        return jsonify({'error': str(e)}), 500


@modeling_bp.route('/api/stl/split', methods=['POST'])
def split_mesh():
    """
    Split/cut mesh along a plane
    """
    try:
        if 'file' not in request.files:
            return jsonify({'error': 'No STL file provided'}), 400

        stl_file = request.files['file']
        mesh = trimesh.load(stl_file, file_type='stl')

        # Get plane parameters
        plane_axis = request.form.get('plane_axis', 'z')  # x, y, or z
        plane_position = float(request.form.get('plane_position', 0))  # position along axis
        keep_part = request.form.get('keep_part', 'both')  # 'positive', 'negative', or 'both'

        # Create plane normal and origin
        plane_normal = np.array([0.0, 0.0, 0.0])
        if plane_axis == 'x':
            plane_normal[0] = 1.0
            plane_origin = np.array([plane_position, 0, 0])
        elif plane_axis == 'y':
            plane_normal[1] = 1.0
            plane_origin = np.array([0, plane_position, 0])
        else:  # z
            plane_normal[2] = 1.0
            plane_origin = np.array([0, 0, plane_position])

        # Slice the mesh
        result_meshes = []

        if keep_part == 'positive' or keep_part == 'both':
            positive_part = mesh.slice_plane(plane_origin, plane_normal, cap=True)
            if positive_part is not None:
                result_meshes.append(('positive', positive_part))

        if keep_part == 'negative' or keep_part == 'both':
            negative_part = mesh.slice_plane(plane_origin, -plane_normal, cap=True)
            if negative_part is not None:
                result_meshes.append(('negative', negative_part))

        # Save result(s)
        download_urls = []
        stats_list = []

        for part_name, part_mesh in result_meshes:
            output_path = os.path.join(current_app.config['UPLOAD_FOLDER'], f'split_{part_name}.stl')
            part_mesh.export(output_path)

            download_urls.append(f'/modeling/download/{os.path.basename(output_path)}')
            stats_list.append({
                'part': part_name,
                'vertices': len(part_mesh.vertices),
                'faces': len(part_mesh.faces),
                'is_watertight': part_mesh.is_watertight
            })

        response_data = {
            'success': True,
            'download_urls': download_urls,
            'stats': stats_list,
            'parts_created': len(result_meshes)
        }

        return jsonify(convert_numpy_types(response_data))

    except Exception as e:
        return jsonify({'error': str(e)}), 500


@modeling_bp.route('/api/stl/array', methods=['POST'])
def array_mesh():
    """
    Create array/pattern of mesh (linear or circular)
    """
    try:
        if 'file' not in request.files:
            return jsonify({'error': 'No STL file provided'}), 400

        stl_file = request.files['file']
        mesh = trimesh.load(stl_file, file_type='stl')

        # Get array parameters
        array_type = request.form.get('array_type', 'linear')  # linear or circular
        count_x = int(request.form.get('count_x', 3))
        count_y = int(request.form.get('count_y', 1))
        spacing_x = float(request.form.get('spacing_x', 50.0))
        spacing_y = float(request.form.get('spacing_y', 50.0))

        # Create array of meshes
        mesh_array = []

        if array_type == 'linear':
            total_copies = count_x * count_y
            if total_copies > MAX_ARRAY_COPIES:
                return jsonify({'error': f'Array too large ({total_copies} copies). Maximum is {MAX_ARRAY_COPIES}.'}), 400

            for i in range(count_x):
                for j in range(count_y):
                    mesh_copy = mesh.copy()
                    translation = np.array([i * spacing_x, j * spacing_y, 0])
                    mesh_copy.apply_translation(translation)
                    mesh_array.append(mesh_copy)

        elif array_type == 'circular':
            count = int(request.form.get('count', 8))
            radius = float(request.form.get('radius', 100.0))

            if count > MAX_ARRAY_COPIES:
                return jsonify({'error': f'Array too large ({count} copies). Maximum is {MAX_ARRAY_COPIES}.'}), 400

            for i in range(count):
                angle = (2 * np.pi * i) / count
                mesh_copy = mesh.copy()

                # Position around circle
                x = radius * np.cos(angle)
                y = radius * np.sin(angle)
                translation = np.array([x, y, 0])
                mesh_copy.apply_translation(translation)

                # Optional: rotate to face center
                if request.form.get('rotate_to_center', 'false').lower() == 'true':
                    rotation_matrix = trimesh.transformations.rotation_matrix(angle + np.pi/2, [0, 0, 1])
                    mesh_copy.apply_transform(rotation_matrix)

                mesh_array.append(mesh_copy)

        # Combine all meshes
        result_mesh = trimesh.util.concatenate(mesh_array)

        # Save result
        output_path = os.path.join(current_app.config['UPLOAD_FOLDER'], f'array_{array_type}.stl')
        result_mesh.export(output_path)

        # Calculate stats
        stats = {
            'vertices': len(result_mesh.vertices),
            'faces': len(result_mesh.faces),
            'is_watertight': result_mesh.is_watertight,
            'copies_created': len(mesh_array),
            'array_type': array_type
        }

        response_data = {
            'success': True,
            'download_url': f'/modeling/download/{os.path.basename(output_path)}',
            'stats': stats
        }

        return jsonify(convert_numpy_types(response_data))

    except Exception as e:
        return jsonify({'error': str(e)}), 500

@modeling_bp.route('/api/generate_shape', methods=['POST'])
def generate_shape():
    """
    Generate parametric 3D shape from scratch

    Expects:
    - shape_type: string (cube, sphere, cylinder, cone, etc.)
    - params: JSON object with shape-specific parameters

    Returns:
    - JSON with download URL and stats
    """
    try:
        data = request.get_json()

        if not data or 'shape_type' not in data:
            return jsonify({'error': 'No shape type provided'}), 400

        shape_type = data['shape_type']
        params = data.get('params', {})

        # Validate parameters
        is_valid, error_msg = validate_shape_params(shape_type, params)
        if not is_valid:
            logger.warning(f"Invalid shape parameters: {error_msg}")
            return jsonify({'error': error_msg}), 400

        # Generate shape
        result = shape_generators.generate_shape(shape_type, params)
        mesh = result['mesh']
        stats = result['stats']

        # Validate mesh size
        is_valid, error_msg = validate_mesh_size(mesh)
        if not is_valid:
            logger.warning(f"Generated mesh too large: {error_msg}")
            return jsonify({'error': error_msg}), 400

        # Save to file
        output_path = os.path.join(current_app.config['UPLOAD_FOLDER'], f'{shape_type}.stl')
        mesh.export(output_path)

        response_data = {
            'success': True,
            'download_url': f'/modeling/download/{os.path.basename(output_path)}',
            'stats': stats
        }

        logger.info(f"Generated shape: {shape_type} with {len(mesh.vertices)} vertices")
        return jsonify(convert_numpy_types(response_data))

    except Exception as e:
        logger.error(f"Error generating shape: {str(e)}")
        return jsonify({'error': str(e)}), 500

# My Models routes
@modeling_bp.route('/api/my_models/list', methods=['GET'])
def list_my_models():
    """List all models in ModelingSaves folder"""
    try:
        my_models_dir = current_app.config.get('MY_MODELS_FOLDER', os.path.join(current_app.config['BASE_DIR'], 'ModelingSaves'))

        if not os.path.exists(my_models_dir):
            os.makedirs(my_models_dir)
            
        models = []
        for filename in os.listdir(my_models_dir):
            if filename.endswith('.stl'):
                filepath = os.path.join(my_models_dir, filename)
                stat = os.stat(filepath)
                models.append({
                    'filename': filename,
                    'name': filename.replace('.stl', ''),
                    'size': stat.st_size,
                    'modified': stat.st_mtime
                })
        
        # Sort by modified time, newest first
        models.sort(key=lambda x: x['modified'], reverse=True)
        
        return jsonify({'success': True, 'models': models})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@modeling_bp.route('/my_models/<filename>', methods=['GET'])
def get_my_model(filename):
    """Serve a model file from ModelingSaves"""
    try:
        my_models_dir = current_app.config.get('MY_MODELS_FOLDER', os.path.join(current_app.config['BASE_DIR'], 'ModelingSaves'))
        filepath = os.path.join(my_models_dir, secure_filename(filename))
        
        if not os.path.exists(filepath):
            return jsonify({'error': 'File not found'}), 404
            
        return send_file(filepath, mimetype='model/stl', as_attachment=False)
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@modeling_bp.route('/api/my_models/save', methods=['POST'])
def save_my_model():
    """Save a model to ModelingSaves folder"""
    try:
        if 'file' not in request.files:
            return jsonify({'success': False, 'error': 'No file provided'}), 400

        file = request.files['file']
        filename = request.form.get('filename', file.filename)
        filename = secure_filename(filename)

        if not filename.endswith('.stl'):
            filename += '.stl'

        my_models_dir = current_app.config.get('MY_MODELS_FOLDER', os.path.join(current_app.config['BASE_DIR'], 'ModelingSaves'))
        if not os.path.exists(my_models_dir):
            os.makedirs(my_models_dir)

        filepath = os.path.join(my_models_dir, filename)
        file.save(filepath)
        
        return jsonify({'success': True, 'filename': filename})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@modeling_bp.route('/api/my_models/delete/<filename>', methods=['DELETE'])
def delete_my_model(filename):
    """Delete a model from ModelingSaves"""
    try:
        my_models_dir = current_app.config.get('MY_MODELS_FOLDER', os.path.join(current_app.config['BASE_DIR'], 'ModelingSaves'))
        filepath = os.path.join(my_models_dir, secure_filename(filename))

        if not os.path.exists(filepath):
            return jsonify({'success': False, 'error': 'File not found'}), 404

        os.remove(filepath)

        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


# ============================================================================
# SCALE/RESIZE TOOL
# ============================================================================

@modeling_bp.route('/api/stl/scale', methods=['POST'])
def scale_stl():
    """
    Scale/resize STL model

    Expects:
    - stl file
    - scale_mode: 'uniform', 'dimensions', 'non_uniform', 'fit', 'volume'
    - Mode-specific parameters

    Returns:
    - Download URL for scaled STL
    """
    try:
        if 'stl' not in request.files:
            return jsonify({'error': 'No STL file provided'}), 400

        file = request.files['stl']
        if file.filename == '':
            return jsonify({'error': 'No file selected'}), 400

        # Save uploaded STL
        upload_path, filename = save_upload(file)

        # Load mesh
        mesh = mesh_utils.load_stl(upload_path)

        # Get parameters
        scale_mode = request.form.get('scale_mode', 'uniform')

        # Build kwargs for scale operation
        kwargs = {}

        if scale_mode == 'uniform':
            kwargs['scale_factor'] = float(request.form.get('scale_factor', 1.0))
        elif scale_mode == 'dimensions':
            if 'target_width' in request.form:
                kwargs['target_width'] = float(request.form.get('target_width'))
            if 'target_height' in request.form:
                kwargs['target_height'] = float(request.form.get('target_height'))
            if 'target_depth' in request.form:
                kwargs['target_depth'] = float(request.form.get('target_depth'))
            kwargs['maintain_aspect'] = request.form.get('maintain_aspect', 'true').lower() == 'true'
        elif scale_mode == 'non_uniform':
            kwargs['scale_x'] = float(request.form.get('scale_x', 1.0))
            kwargs['scale_y'] = float(request.form.get('scale_y', 1.0))
            kwargs['scale_z'] = float(request.form.get('scale_z', 1.0))
        elif scale_mode == 'fit':
            kwargs['max_dimension'] = float(request.form.get('max_dimension', 100.0))
            kwargs['maintain_aspect'] = request.form.get('maintain_aspect', 'true').lower() == 'true'
        elif scale_mode == 'volume':
            kwargs['target_volume'] = float(request.form.get('target_volume', 1000.0))

        # Perform scaling
        result = scale.scale_mesh(mesh, scale_mode=scale_mode, **kwargs)

        # Save result
        output_filename = f"scaled_{os.path.splitext(filename)[0]}.stl"
        output_path = os.path.join(current_app.config['OUTPUT_FOLDER'], output_filename)
        mesh_utils.save_stl(result['mesh'], output_path)

        response_data = {
            'success': True,
            'download_url': f'/modeling/download/{output_filename}',
            'stats': result['stats']
        }

        return jsonify(convert_numpy_types(response_data))

    except Exception as e:
        logger.error(f"Error scaling mesh: {e}")
        return jsonify({'error': str(e)}), 500


# ============================================================================
# CUT/PLANE CUT TOOL
# ============================================================================

@modeling_bp.route('/api/stl/cut', methods=['POST'])
def cut_stl():
    """
    Cut STL model with a plane

    Expects:
    - stl file
    - cut_mode: 'plane', 'height', 'remove_top', 'remove_bottom', 'split'
    - Mode-specific parameters

    Returns:
    - Download URL(s) for cut STL
    """
    try:
        if 'stl' not in request.files:
            return jsonify({'error': 'No STL file provided'}), 400

        file = request.files['stl']
        if file.filename == '':
            return jsonify({'error': 'No file selected'}), 400

        # Save uploaded STL
        upload_path, filename = save_upload(file)

        # Load mesh
        mesh = mesh_utils.load_stl(upload_path)

        # Get parameters
        cut_mode = request.form.get('cut_mode', 'plane')

        # Build kwargs for cut operation
        kwargs = {}

        if cut_mode == 'plane':
            kwargs['plane_axis'] = request.form.get('plane_axis', 'z')
            kwargs['plane_position'] = float(request.form.get('plane_position', 50.0))
            kwargs['position_mode'] = request.form.get('position_mode', 'percentage')
            kwargs['keep_part'] = request.form.get('keep_part', 'bottom')
            kwargs['cap_cut'] = request.form.get('cap_cut', 'true').lower() == 'true'
        elif cut_mode == 'height':
            kwargs['height_mm'] = float(request.form.get('height_mm', 10.0))
            kwargs['from_bottom'] = request.form.get('from_bottom', 'true').lower() == 'true'
            kwargs['keep_part'] = request.form.get('keep_part', 'bottom')
        elif cut_mode == 'remove_top':
            kwargs['amount_mm'] = float(request.form.get('amount_mm', 5.0))
        elif cut_mode == 'remove_bottom':
            kwargs['amount_mm'] = float(request.form.get('amount_mm', 5.0))
        elif cut_mode == 'split':
            kwargs['axis'] = request.form.get('axis', 'z')
            kwargs['offset'] = float(request.form.get('offset', 0.0))

        # Perform cut
        result = cut.cut_mesh(mesh, cut_mode=cut_mode, **kwargs)

        # Handle result
        if isinstance(result['mesh'], list):
            # Multiple parts (split mode)
            download_urls = []
            for part_name, part_mesh in result['mesh']:
                output_filename = f"cut_{part_name}_{os.path.splitext(filename)[0]}.stl"
                output_path = os.path.join(current_app.config['OUTPUT_FOLDER'], output_filename)
                mesh_utils.save_stl(part_mesh, output_path)
                download_urls.append(f'/modeling/download/{output_filename}')

            response_data = {
                'success': True,
                'download_urls': download_urls,
                'stats': result['stats']
            }
        else:
            # Single part
            output_filename = f"cut_{os.path.splitext(filename)[0]}.stl"
            output_path = os.path.join(current_app.config['OUTPUT_FOLDER'], output_filename)
            mesh_utils.save_stl(result['mesh'], output_path)

            response_data = {
                'success': True,
                'download_url': f'/modeling/download/{output_filename}',
                'stats': result['stats']
            }

        return jsonify(convert_numpy_types(response_data))

    except Exception as e:
        logger.error(f"Error cutting mesh: {e}")
        return jsonify({'error': str(e)}), 500


# ============================================================================
# CHANNEL/GROOVE CARVING TOOL
# ============================================================================

@modeling_bp.route('/api/stl/channels', methods=['POST'])
def add_channels_stl():
    """
    Add channels/grooves to STL model

    Expects:
    - stl file
    - channel_type: 'linear', 'radial', 'spiral', 'grid', 'path'
    - Channel-specific parameters

    Returns:
    - Download URL for mesh with channels
    """
    try:
        if 'stl' not in request.files:
            return jsonify({'error': 'No STL file provided'}), 400

        file = request.files['stl']
        if file.filename == '':
            return jsonify({'error': 'No file selected'}), 400

        # Save uploaded STL
        upload_path, filename = save_upload(file)

        # Load mesh
        mesh = mesh_utils.load_stl(upload_path)

        # Get parameters
        channel_type = request.form.get('channel_type', 'radial')

        # Build kwargs based on channel type
        import json
        kwargs = {
            'width': float(request.form.get('width', 2.0)),
            'depth': float(request.form.get('depth', 1.0))
        }

        if channel_type == 'radial':
            kwargs['center_point'] = json.loads(request.form.get('center_point', '[0, 0, 0]'))
            kwargs['radius'] = float(request.form.get('radius', 20.0))
            kwargs['num_channels'] = int(request.form.get('num_channels', 8))
        elif channel_type == 'linear':
            kwargs['start_point'] = json.loads(request.form.get('start_point', '[0, 0, 0]'))
            kwargs['end_point'] = json.loads(request.form.get('end_point', '[10, 0, 0]'))
            kwargs['profile'] = request.form.get('profile', 'v')
        elif channel_type == 'spiral':
            kwargs['center_point'] = json.loads(request.form.get('center_point', '[0, 0, 0]'))
            kwargs['start_radius'] = float(request.form.get('start_radius', 5.0))
            kwargs['end_radius'] = float(request.form.get('end_radius', 20.0))
            kwargs['rotations'] = float(request.form.get('rotations', 2.0))
        elif channel_type == 'grid':
            kwargs['bounds'] = json.loads(request.form.get('bounds', '[-20, 20, -20, 20]'))
            kwargs['z_height'] = float(request.form.get('z_height', 0.0))
            kwargs['spacing_x'] = float(request.form.get('spacing_x', 10.0))
            kwargs['spacing_y'] = float(request.form.get('spacing_y', 10.0))

        # Perform channel carving
        result = channels.add_channels(mesh, channel_type=channel_type, **kwargs)

        # Save result
        output_filename = f"channels_{os.path.splitext(filename)[0]}.stl"
        output_path = os.path.join(current_app.config['OUTPUT_FOLDER'], output_filename)
        mesh_utils.save_stl(result['mesh'], output_path)

        response_data = {
            'success': True,
            'download_url': f'/modeling/download/{output_filename}',
            'stats': result['stats']
        }

        return jsonify(convert_numpy_types(response_data))

    except Exception as e:
        logger.error(f"Error adding channels: {e}")
        return jsonify({'error': str(e)}), 500

# ============================================================================
# BACKGROUND TASK ROUTES - Async Processing with Progress Tracking
# ============================================================================

@modeling_bp.route('/api/generate_async', methods=['POST'])
def generate_async():
    """
    Generate cookie cutter asynchronously using Celery background task
    Returns task_id for progress tracking
    """
    if not CELERY_AVAILABLE:
        return jsonify({'error': 'Background tasks not available - please start Celery'}), 503
    
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
        upload_path, filename = save_upload(file)

        # Get default parameters from config
        defaults = current_app.config.get('COOKIE_CUTTER_DEFAULTS', {})

        # Get parameters from request
        params = {
            'blade_thick': float(request.form.get('blade_thick', defaults.get('blade_thick', 2.0))),
            'blade_height': float(request.form.get('blade_height', defaults.get('blade_height', 20.0))),
            'base_thick': float(request.form.get('base_thick', defaults.get('base_thick', 3.0))),
            'base_extra': float(request.form.get('base_extra', defaults.get('base_extra', 10.0))),
            'max_dim': float(request.form.get('max_dim', defaults.get('max_dim', 90.0))),
            'no_base': request.form.get('no_base', 'false').lower() == 'true',
            'detail_level': float(request.form.get('detail_level', 0.5))
        }

        # Validate parameters
        is_valid, error_msg = validate_params(params)
        if not is_valid:
            return jsonify({'error': f'Invalid parameter: {error_msg}'}), 400
        
        # Launch background task
        output_folder = current_app.config['OUTPUT_FOLDER']
        task = generate_cookie_cutter_task.delay(upload_path, params, output_folder)
        
        return jsonify({
            'success': True,
            'task_id': task.id,
            'message': 'Generation started in background. Check /api/task_status/{task_id} for progress.'
        })
    
    except Exception as e:
        logger.error(f"Error starting async generation: {e}")
        return jsonify({'error': str(e)}), 500


@modeling_bp.route('/api/stl/thicken_async', methods=['POST'])
def thicken_async():
    """
    Thicken mesh walls asynchronously using Celery background task
    Returns task_id for progress tracking
    """
    if not CELERY_AVAILABLE:
        return jsonify({'error': 'Background tasks not available - please start Celery'}), 503
    
    try:
        if 'stl' not in request.files:
            return jsonify({'error': 'No STL file provided'}), 400
        
        file = request.files['stl']
        if file.filename == '':
            return jsonify({'error': 'No file selected'}), 400
        
        # Save uploaded file
        input_path, filename = save_upload(file)
        
        # Get parameters
        params = {
            'offset': float(request.form.get('offset', 2.0)),
            'smooth': request.form.get('smooth', 'true').lower() == 'true',
            'selected_faces': request.form.get('selected_faces')
        }
        
        # Launch background task
        output_folder = current_app.config['OUTPUT_FOLDER']
        task = thicken_mesh_task.delay(input_path, params, output_folder)
        
        return jsonify({
            'success': True,
            'task_id': task.id,
            'message': 'Thickening started in background.'
        })
    
    except Exception as e:
        logger.error(f"Error starting async thickening: {e}")
        return jsonify({'error': str(e)}), 500


@modeling_bp.route('/api/stl/hollow_async', methods=['POST'])
def hollow_async():
    """
    Hollow out mesh asynchronously using Celery background task
    Returns task_id for progress tracking
    """
    if not CELERY_AVAILABLE:
        return jsonify({'error': 'Background tasks not available - please start Celery'}), 503
    
    try:
        if 'stl' not in request.files:
            return jsonify({'error': 'No STL file provided'}), 400
        
        file = request.files['stl']
        if file.filename == '':
            return jsonify({'error': 'No file selected'}), 400
        
        # Save uploaded file
        input_path, filename = save_upload(file)
        
        # Get parameters
        params = {
            'wall_thickness': float(request.form.get('wall_thickness', 2.0)),
            'add_drainage': request.form.get('add_drainage', 'true').lower() == 'true',
            'drain_diameter': float(request.form.get('drain_diameter', 5.0))
        }
        
        # Launch background task
        output_folder = current_app.config['OUTPUT_FOLDER']
        task = hollow_mesh_task.delay(input_path, params, output_folder)
        
        return jsonify({
            'success': True,
            'task_id': task.id,
            'message': 'Hollowing started in background.'
        })
    
    except Exception as e:
        logger.error(f"Error starting async hollowing: {e}")
        return jsonify({'error': str(e)}), 500


@modeling_bp.route('/api/task_status/<task_id>')
def task_status(task_id):
    """
    Check status of a background task
    
    Returns:
        {
            'state': 'PENDING' | 'PROGRESS' | 'SUCCESS' | 'FAILURE',
            'current': <progress value>,
            'total': <total value>,
            'status': <status message>,
            'result': <task result if completed>
        }
    """
    if not CELERY_AVAILABLE:
        return jsonify({'error': 'Background tasks not available'}), 503
    
    try:
        from celery.result import AsyncResult
        task = AsyncResult(task_id)
        
        if task.state == 'PENDING':
            response = {
                'state': task.state,
                'current': 0,
                'total': 100,
                'status': 'Waiting to start...'
            }
        elif task.state == 'PROGRESS':
            response = {
                'state': task.state,
                'current': task.info.get('current', 0),
                'total': task.info.get('total', 100),
                'status': task.info.get('status', 'Processing...')
            }
        elif task.state == 'SUCCESS':
            response = {
                'state': task.state,
                'current': 100,
                'total': 100,
                'status': 'Complete!',
                'result': task.result
            }
        elif task.state == 'FAILURE':
            response = {
                'state': task.state,
                'current': 100,
                'total': 100,
                'status': str(task.info),
                'error': str(task.info)
            }
        else:
            response = {
                'state': task.state,
                'current': 50,
                'total': 100,
                'status': str(task.state)
            }
        
        return jsonify(response)
    
    except Exception as e:
        logger.error(f"Error checking task status: {e}")
        return jsonify({'error': str(e)}), 500


@modeling_bp.route('/api/stl/widen_hole', methods=['POST'])
def widen_hole_route():
    """
    Widen a cylindrical hole in an STL mesh

    Expects:
    - stl file
    - new_radius: Desired new radius (mm)
    - auto_detect: Boolean (default True) - auto-detect hole or use manual params
    - center: Optional [x, y, z] for manual mode
    - axis: Optional 0|1|2 (X|Y|Z) for manual mode
    - current_radius: Optional current radius for manual mode
    - height_min: Optional minimum height for partial widening
    - height_max: Optional maximum height for partial widening

    Returns:
    - JSON with download URL or error
    """
    try:
        # Check if STL file was uploaded
        if 'stl' not in request.files:
            return jsonify({'error': 'No STL file provided'}), 400

        file = request.files['stl']
        if file.filename == '':
            return jsonify({'error': 'No file selected'}), 400

        # Save uploaded file
        upload_path, filename = save_upload(file)

        # Load mesh
        mesh = trimesh.load(upload_path)

        # Get parameters
        new_radius = float(request.form.get('new_radius', 5.0))
        auto_detect = request.form.get('auto_detect', 'true').lower() == 'true'

        # Optional manual parameters
        center = None
        if 'center' in request.form:
            center = np.array([float(x) for x in request.form.get('center').split(',')])

        axis = int(request.form.get('axis', 2))  # Default Z-axis
        current_radius = None
        if 'current_radius' in request.form:
            current_radius = float(request.form.get('current_radius'))

        # Optional height range for partial widening
        height_range = None
        if 'height_min' in request.form and 'height_max' in request.form:
            height_min = float(request.form.get('height_min'))
            height_max = float(request.form.get('height_max'))
            height_range = (height_min, height_max)

        # Widen hole
        result = bore_hole.widen_hole(
            mesh=mesh,
            new_radius=new_radius,
            auto_detect=auto_detect,
            center=center,
            axis=axis,
            current_radius=current_radius,
            height_range=height_range
        )

        result_mesh = result['mesh']
        stats = result['stats']

        # Save result
        output_filename = f"widened_{filename}"
        output_path = os.path.join(current_app.config['OUTPUT_FOLDER'], output_filename)
        result_mesh.export(output_path)

        # Convert numpy types for JSON
        stats = convert_numpy_types(stats)

        return jsonify({
            'success': True,
            'download_url': f'/modeling/download/{output_filename}',
            'stats': stats
        })

    except Exception as e:
        logger.error(f"Error widening hole: {str(e)}")
        return jsonify({'error': str(e)}), 500


@modeling_bp.route('/api/stl/detect_holes', methods=['POST'])
def detect_holes_route():
    """
    Detect holes in an STL mesh

    Expects:
    - stl file
    - min_radius: Optional minimum radius (default 1.0)
    - max_radius: Optional maximum radius (default 50.0)

    Returns:
    - JSON with detected holes information
    """
    try:
        # Check if STL file was uploaded
        if 'stl' not in request.files:
            return jsonify({'error': 'No STL file provided'}), 400

        file = request.files['stl']
        if file.filename == '':
            return jsonify({'error': 'No file selected'}), 400

        # Save uploaded file
        upload_path, filename = save_upload(file)

        # Load mesh
        mesh = trimesh.load(upload_path)

        # Get parameters
        min_radius = float(request.form.get('min_radius', 1.0))
        max_radius = float(request.form.get('max_radius', 50.0))

        # Detect holes
        hole_info = bore_hole.get_hole_info(mesh)

        # Convert numpy types for JSON
        hole_info = convert_numpy_types(hole_info)

        return jsonify({
            'success': True,
            'hole_info': hole_info
        })

    except Exception as e:
        logger.error(f"Error detecting holes: {str(e)}")
        return jsonify({'error': str(e)}), 500


# ============================================================================
# BROWSE FILES ENDPOINTS
# ============================================================================

@modeling_bp.route('/modeling/api/browse/stls', methods=['GET'])
def browse_stls():
    """Browse saved STL files"""
    try:
        stl_folder = os.path.join(current_app.root_path, 'programs/Modeling/ModelingSaves/STLs')

        if not os.path.exists(stl_folder):
            return jsonify({'success': True, 'files': []})

        files = []
        for filename in os.listdir(stl_folder):
            if filename.lower().endswith('.stl'):
                filepath = os.path.join(stl_folder, filename)
                file_size = os.path.getsize(filepath)
                files.append({
                    'filename': filename,
                    'size': file_size,
                    'url': f'/modeling/ModelingSaves/STLs/{filename}'
                })

        # Sort by filename
        files.sort(key=lambda x: x['filename'])

        return jsonify({
            'success': True,
            'files': files
        })

    except Exception as e:
        logger.error(f"Error browsing STL files: {str(e)}")
        return jsonify({'error': str(e)}), 500


@modeling_bp.route('/modeling/api/browse/images', methods=['GET'])
def browse_images():
    """Browse saved image files"""
    try:
        image_folder = os.path.join(current_app.root_path, 'programs/Modeling/ModelingSaves/Images')

        if not os.path.exists(image_folder):
            return jsonify({'success': True, 'files': []})

        files = []
        image_extensions = {'.png', '.jpg', '.jpeg', '.webp', '.gif', '.bmp'}

        for filename in os.listdir(image_folder):
            ext = os.path.splitext(filename)[1].lower()
            if ext in image_extensions:
                filepath = os.path.join(image_folder, filename)
                file_size = os.path.getsize(filepath)
                files.append({
                    'filename': filename,
                    'size': file_size,
                    'url': f'/modeling/ModelingSaves/Images/{filename}'
                })

        # Sort by filename
        files.sort(key=lambda x: x['filename'])

        return jsonify({
            'success': True,
            'files': files
        })

    except Exception as e:
        logger.error(f"Error browsing image files: {str(e)}")
        return jsonify({'error': str(e)}), 500


# ============================================================================
# SHAPE GENERATOR ENDPOINT
# ============================================================================

@modeling_bp.route('/modeling/api/generate/shape', methods=['POST'])
def generate_shape_api():
    """Generate parametric shapes"""
    try:
        shape_type = request.form.get('shape_type')

        if not shape_type:
            return jsonify({'error': 'No shape type specified'}), 400

        # Collect parameters
        params = {}
        for key in request.form:
            if key != 'shape_type':
                value = request.form.get(key)
                # Try to convert to appropriate type
                try:
                    if value.lower() in ('true', 'false'):
                        params[key] = value.lower() == 'true'
                    elif '.' in value:
                        params[key] = float(value)
                    else:
                        params[key] = int(value)
                except (ValueError, AttributeError):
                    params[key] = value

        # Generate the shape
        mesh = shape_generators.generate_shape(shape_type, params)

        # Save the result
        output_filename = f"{shape_type}_{hash(str(params)) % 1000000}.stl"
        output_path = os.path.join(current_app.config['OUTPUT_FOLDER'], output_filename)
        mesh.export(output_path)

        download_url = f'/modeling/download/{output_filename}'

        # Get stats
        stats = {
            'vertices': len(mesh.vertices),
            'faces': len(mesh.faces),
            'volume': float(mesh.volume),
            'surface_area': float(mesh.area)
        }

        return jsonify({
            'success': True,
            'download_url': download_url,
            'filename': output_filename,
            'stats': stats
        })

    except Exception as e:
        logger.error(f"Error generating shape: {str(e)}")
        return jsonify({'error': str(e)}), 500


# ============================================================================
# FIDGET TOY GENERATOR ENDPOINT
# ============================================================================

@modeling_bp.route('/modeling/api/generate/fidget', methods=['POST'])
def generate_fidget_api():
    """Generate fidget toys"""
    try:
        fidget_type = request.form.get('fidget_type')

        if not fidget_type:
            return jsonify({'error': 'No fidget type specified'}), 400

        # Collect parameters
        params = {}
        for key in request.form:
            if key != 'fidget_type':
                value = request.form.get(key)
                # Try to convert to appropriate type
                try:
                    if value.lower() in ('true', 'false'):
                        params[key] = value.lower() == 'true'
                    elif '.' in value:
                        params[key] = float(value)
                    else:
                        params[key] = int(value)
                except (ValueError, AttributeError):
                    params[key] = value

        # Create generator instance
        generator = fidget_generators.FidgetGenerators()

        # Generate based on type
        if fidget_type == 'flexi_worm':
            mesh = generator.flexi_worm(
                length=params.get('length', 100.0),
                diameter=params.get('diameter', 15.0),
                num_segments=params.get('num_segments', 20),
                flex_gap=params.get('flex_gap', 0.3)
            )
        elif fidget_type == 'interlocking_rings':
            mesh = generator.interlocking_rings(
                ring_diameter=params.get('ring_diameter', 30.0),
                ring_thickness=params.get('ring_thickness', 3.0),
                num_rings=params.get('num_rings', 5),
                ring_type=params.get('ring_type', 'circular')
            )
        elif fidget_type == 'fidget_spinner':
            mesh = generator.fidget_spinner(
                center_diameter=params.get('center_diameter', 22.0),
                bearing_diameter=params.get('bearing_diameter', 8.0),
                num_weights=params.get('num_weights', 3)
            )
        elif fidget_type == 'gear_fidget':
            mesh = generator.gear_fidget(
                num_teeth=params.get('num_teeth', 12),
                outer_radius=params.get('outer_radius', 25.0),
                num_gears=params.get('num_gears', 3)
            )
        elif fidget_type == 'chain_link':
            mesh = generator.chain_link(
                link_length=params.get('link_length', 30.0),
                link_width=params.get('link_width', 15.0),
                num_links=params.get('num_links', 5)
            )
        elif fidget_type == 'pop_it_bubble':
            # Parse grid_size tuple
            grid_size_str = params.get('grid_size', '(5, 5)')
            grid_size = eval(grid_size_str)  # Safe here since we control the input

            mesh = generator.pop_it_bubble(
                bubble_diameter=params.get('bubble_diameter', 15.0),
                grid_size=grid_size
            )
        else:
            return jsonify({'error': f'Unknown fidget type: {fidget_type}'}), 400

        # Save the result
        output_filename = f"{fidget_type}_{hash(str(params)) % 1000000}.stl"
        output_path = os.path.join(current_app.config['OUTPUT_FOLDER'], output_filename)
        mesh.export(output_path)

        download_url = f'/modeling/download/{output_filename}'

        # Get stats
        stats = {
            'vertices': len(mesh.vertices),
            'faces': len(mesh.faces),
            'volume': float(mesh.volume),
            'surface_area': float(mesh.area)
        }

        return jsonify({
            'success': True,
            'download_url': download_url,
            'filename': output_filename,
            'stats': stats
        })

    except Exception as e:
        logger.error(f"Error generating fidget: {str(e)}")
        return jsonify({'error': str(e)}), 500
