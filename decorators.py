#!/usr/bin/env python3
"""
ZoolZ Decorators - Reusable patterns for route handling
Eliminates duplicate code and makes routes cleaner
"""

import os
import logging
from functools import wraps
from flask import request, jsonify, current_app
from werkzeug.utils import secure_filename
import trimesh

logger = logging.getLogger(__name__)


# ============================================================================
# FILE UPLOAD DECORATORS
# ============================================================================

def requires_stl_file(param_name='stl'):
    """
    Decorator to handle STL file upload boilerplate.

    Usage:
        @modeling_bp.route('/api/stl/scale', methods=['POST'])
        @requires_stl_file('stl')
        def scale_stl(stl_file, stl_path, mesh):
            # Just focus on scaling logic!
            # stl_file = uploaded file object
            # stl_path = path where file was saved
            # mesh = loaded trimesh object
            pass
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            # Check file exists in request
            if param_name not in request.files:
                return jsonify({'error': f'No {param_name} file provided'}), 400

            file = request.files[param_name]
            if file.filename == '':
                return jsonify({'error': 'No file selected'}), 400

            # Validate file type
            if not file.filename.lower().endswith('.stl'):
                return jsonify({'error': 'File must be an STL'}), 400

            # Save file
            filename = secure_filename(file.filename)
            upload_path = os.path.join(current_app.config['UPLOAD_FOLDER'], filename)

            try:
                file.save(upload_path)
            except Exception as e:
                logger.error(f"Error saving file: {e}")
                return jsonify({'error': 'Failed to save file'}), 500

            # Load mesh
            try:
                mesh = trimesh.load(upload_path, file_type='stl')
            except Exception as e:
                logger.error(f"Error loading STL: {e}")
                return jsonify({'error': 'Invalid STL file'}), 400

            # Validate mesh size
            if len(mesh.vertices) > current_app.config.get('MAX_MESH_VERTICES', 10000000):
                return jsonify({'error': 'Mesh too large (too many vertices)'}), 400

            # Call the actual function with the file, path, and mesh
            kwargs[f'{param_name}_file'] = file
            kwargs[f'{param_name}_path'] = upload_path
            kwargs['mesh'] = mesh

            return f(*args, **kwargs)

        return decorated_function
    return decorator


def requires_image_file(param_name='image'):
    """
    Decorator to handle image file upload boilerplate.

    Usage:
        @modeling_bp.route('/api/generate', methods=['POST'])
        @requires_image_file('image')
        def generate(image_file, image_path):
            # Just focus on generation logic!
            pass
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            # Check file exists in request
            if param_name not in request.files:
                return jsonify({'error': f'No {param_name} file provided'}), 400

            file = request.files[param_name]
            if file.filename == '':
                return jsonify({'error': 'No file selected'}), 400

            # Validate file type
            allowed_extensions = current_app.config.get('ALLOWED_IMAGE_EXTENSIONS',
                                                       {'png', 'jpg', 'jpeg', 'gif', 'bmp', 'webp'})
            if not ('.' in file.filename and
                    file.filename.rsplit('.', 1)[1].lower() in allowed_extensions):
                return jsonify({'error': 'Invalid image type'}), 400

            # Validate file size
            file.seek(0, os.SEEK_END)
            file_size = file.tell()
            file.seek(0)

            max_size = current_app.config.get('MAX_CONTENT_LENGTH', 100 * 1024 * 1024)
            if file_size > max_size:
                return jsonify({'error': f'File too large (max {max_size // 1024 // 1024}MB)'}), 400

            # Save file
            filename = secure_filename(file.filename)
            upload_path = os.path.join(current_app.config['UPLOAD_FOLDER'], filename)

            try:
                file.save(upload_path)
            except Exception as e:
                logger.error(f"Error saving file: {e}")
                return jsonify({'error': 'Failed to save file'}), 500

            # Call the actual function with the file and path
            kwargs[f'{param_name}_file'] = file
            kwargs[f'{param_name}_path'] = upload_path

            return f(*args, **kwargs)

        return decorated_function
    return decorator


# ============================================================================
# ERROR HANDLING DECORATORS
# ============================================================================

def handle_errors(f):
    """
    Decorator to handle exceptions consistently.

    Usage:
        @modeling_bp.route('/api/some_route')
        @handle_errors
        def some_route():
            # If this raises an exception, it's automatically handled
            pass
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        try:
            return f(*args, **kwargs)
        except ValueError as e:
            # User error (bad input)
            logger.warning(f"Validation error in {f.__name__}: {e}")
            return jsonify({'error': str(e)}), 400
        except FileNotFoundError as e:
            logger.error(f"File not found in {f.__name__}: {e}")
            return jsonify({'error': 'File not found'}), 404
        except Exception as e:
            # Server error
            logger.error(f"Error in {f.__name__}: {e}", exc_info=True)
            return jsonify({'error': 'Internal server error'}), 500

    return decorated_function


# ============================================================================
# VALIDATION DECORATORS
# ============================================================================

def validate_params(schema):
    """
    Decorator to validate request parameters.

    Usage:
        from marshmallow import Schema, fields

        class ScaleSchema(Schema):
            scale_factor = fields.Float(required=True, validate=lambda x: 0.1 <= x <= 10)

        @modeling_bp.route('/api/scale')
        @validate_params(ScaleSchema())
        def scale(validated_data):
            scale_factor = validated_data['scale_factor']
            pass
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            # Get data from request (form data or JSON)
            if request.is_json:
                data = request.get_json()
            else:
                data = request.form.to_dict()

            # Validate
            errors = schema.validate(data)
            if errors:
                return jsonify({'error': 'Validation failed', 'details': errors}), 400

            # Load and pass validated data
            validated_data = schema.load(data)
            kwargs['validated_data'] = validated_data

            return f(*args, **kwargs)

        return decorated_function
    return decorator


# ============================================================================
# RESPONSE FORMATTING DECORATORS
# ============================================================================

def json_response(f):
    """
    Decorator to automatically convert return values to JSON responses.

    Usage:
        @modeling_bp.route('/api/something')
        @json_response
        def something():
            return {'success': True, 'data': 'hello'}
            # Automatically becomes: jsonify(...), 200
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        result = f(*args, **kwargs)

        # If already a Response object, return as-is
        if hasattr(result, 'status_code'):
            return result

        # If tuple (data, status_code), unpack
        if isinstance(result, tuple):
            data, status_code = result
            return jsonify(data), status_code

        # Otherwise, return as JSON with 200
        return jsonify(result), 200

    return decorated_function


# ============================================================================
# LOGGING DECORATORS
# ============================================================================

def log_execution(f):
    """
    Decorator to log function execution (useful for debugging).

    Usage:
        @modeling_bp.route('/api/something')
        @log_execution
        def something():
            pass
            # Logs: "Executing something with args=..., kwargs=..."
            # Logs: "Completed something in 1.23s"
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        import time
        start_time = time.time()

        logger.info(f"Executing {f.__name__} with args={args}, kwargs={kwargs}")

        result = f(*args, **kwargs)

        elapsed = time.time() - start_time
        logger.info(f"Completed {f.__name__} in {elapsed:.2f}s")

        return result

    return decorated_function


# ============================================================================
# COMBINED DECORATORS (Common Patterns)
# ============================================================================

def stl_operation(f):
    """
    Combined decorator for common STL operations.
    Handles: file upload, error handling, JSON response, logging

    Usage:
        @modeling_bp.route('/api/stl/my_operation', methods=['POST'])
        @stl_operation
        def my_operation(mesh, stl_path):
            # Just write your logic!
            result_mesh = do_something(mesh)

            # Save and return
            output_path = save_mesh(result_mesh)
            return {'success': True, 'download_url': output_path}
    """
    @wraps(f)
    @requires_stl_file('stl')
    @handle_errors
    @json_response
    @log_execution
    def decorated_function(*args, **kwargs):
        return f(*args, **kwargs)

    return decorated_function


def image_operation(f):
    """
    Combined decorator for image-based operations.
    Handles: image upload, error handling, JSON response, logging

    Usage:
        @modeling_bp.route('/api/generate', methods=['POST'])
        @image_operation
        def generate(image_path):
            # Just write your logic!
            result = generate_something(image_path)
            return {'success': True, 'result': result}
    """
    @wraps(f)
    @requires_image_file('image')
    @handle_errors
    @json_response
    @log_execution
    def decorated_function(*args, **kwargs):
        return f(*args, **kwargs)

    return decorated_function


# ============================================================================
# USAGE EXAMPLES
# ============================================================================

"""
BEFORE (lots of duplicate code):

@modeling_bp.route('/api/stl/scale', methods=['POST'])
def scale_stl():
    if 'stl' not in request.files:
        return jsonify({'error': 'No STL file provided'}), 400

    file = request.files['stl']
    if file.filename == '':
        return jsonify({'error': 'No file selected'}), 400

    filename = secure_filename(file.filename)
    upload_path = os.path.join(current_app.config['UPLOAD_FOLDER'], filename)
    file.save(upload_path)

    try:
        mesh = trimesh.load(upload_path, file_type='stl')
    except Exception as e:
        return jsonify({'error': 'Invalid STL'}), 400

    try:
        # Your actual logic is buried here
        scaled_mesh = scale.scale_mesh(mesh, factor=2.0)
        # Save and return...
    except Exception as e:
        return jsonify({'error': str(e)}), 500


AFTER (clean and simple):

@modeling_bp.route('/api/stl/scale', methods=['POST'])
@stl_operation
def scale_stl(mesh, stl_path):
    # Just your logic!
    scale_factor = float(request.form.get('scale_factor', 2.0))
    result = scale.scale_mesh_uniform(mesh, scale_factor=scale_factor)

    # Save
    output_filename = f"scaled_{os.path.basename(stl_path)}"
    output_path = os.path.join(current_app.config['OUTPUT_FOLDER'], output_filename)
    result['mesh'].export(output_path)

    return {
        'success': True,
        'download_url': f'/modeling/download/{output_filename}',
        'stats': result['stats']
    }

50+ lines → 15 lines! 🎉
"""
