#!/usr/bin/env python3
"""
ZoolZ Background Tasks - Celery Configuration
Handles long-running operations without blocking Flask
"""

import os
import logging
from celery import Celery
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Initialize Celery
celery = Celery(
    'zoolz',
    broker=os.getenv('CELERY_BROKER_URL', 'redis://localhost:6379/0'),
    backend=os.getenv('CELERY_RESULT_BACKEND', 'redis://localhost:6379/0')
)

# Celery configuration
celery.conf.update(
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    timezone='UTC',
    enable_utc=True,
    task_track_started=True,
    task_time_limit=int(os.getenv('CELERY_TASK_TIMEOUT', 600)),  # 10 minutes max
    task_soft_time_limit=int(os.getenv('CELERY_TASK_TIMEOUT', 600)) - 30,
    worker_max_tasks_per_child=50,  # Restart worker after 50 tasks (prevent memory leaks)
    worker_prefetch_multiplier=1,  # Only fetch one task at a time
)

logger = logging.getLogger(__name__)


# ============================================================================
# COOKIE CUTTER GENERATION - Background Task
# ============================================================================

@celery.task(bind=True, name='tasks.generate_cookie_cutter')
def generate_cookie_cutter_task(self, upload_path, params, output_folder):
    """
    Generate cookie cutter in background.

    Args:
        self: Task instance (for progress updates)
        upload_path: Path to uploaded image
        params: Cookie cutter parameters
        output_folder: Where to save the STL

    Returns:
        dict: Result with download_url and stats
    """
    try:
        # Import here to avoid circular imports and load only when needed
        from shared.cookie_logic import generate_cookie_cutter
        import os
        from werkzeug.utils import secure_filename

        # Update progress: Starting
        self.update_state(
            state='PROGRESS',
            meta={'current': 10, 'total': 100, 'status': 'Processing image...'}
        )

        logger.info(f"Starting cookie cutter generation: {upload_path}")

        # Generate the cookie cutter
        result = generate_cookie_cutter(
            upload_path,
            detail_level=params.get('detail_level', 0.5),
            blade_thick=params.get('blade_thick', 2.0),
            blade_height=params.get('blade_height', 20.0),
            base_thick=params.get('base_thick', 3.0),
            base_extra=params.get('base_extra', 10.0),
            max_dim=params.get('max_dim', 90.0),
            no_base=params.get('no_base', False)
        )

        # Update progress: Generated mesh
        self.update_state(
            state='PROGRESS',
            meta={'current': 70, 'total': 100, 'status': 'Saving STL file...'}
        )

        # Save the result
        mesh = result['mesh']
        input_filename = os.path.basename(upload_path)
        output_filename = secure_filename(f"cookie_{input_filename}.stl")
        output_path = os.path.join(output_folder, output_filename)

        mesh.export(output_path)

        # Update progress: Complete
        self.update_state(
            state='PROGRESS',
            meta={'current': 100, 'total': 100, 'status': 'Complete!'}
        )

        logger.info(f"Cookie cutter generated successfully: {output_path}")

        # Return result
        return {
            'success': True,
            'download_url': f'/modeling/download/{output_filename}',
            'output_path': output_path,
            'stats': result.get('stats', {}),
            'message': 'Cookie cutter generated successfully!'
        }

    except Exception as e:
        logger.error(f"Cookie cutter generation failed: {e}", exc_info=True)
        self.update_state(
            state='FAILURE',
            meta={'error': str(e), 'status': 'Failed'}
        )
        return {
            'success': False,
            'error': str(e)
        }


# ============================================================================
# STL OPERATIONS - Background Tasks
# ============================================================================

@celery.task(bind=True, name='tasks.thicken_mesh')
def thicken_mesh_task(self, input_path, params, output_folder):
    """Thicken mesh walls in background"""
    try:
        from programs.modeling.utils import thicken, mesh_utils
        import os
        from werkzeug.utils import secure_filename

        self.update_state(state='PROGRESS', meta={'current': 20, 'total': 100, 'status': 'Loading mesh...'})

        mesh = mesh_utils.load_stl(input_path)

        self.update_state(state='PROGRESS', meta={'current': 40, 'total': 100, 'status': 'Thickening walls...'})

        result = thicken.thicken_mesh(
            mesh,
            thickness_mm=float(params.get('thickness', 2.0)),
            mode=params.get('mode', 'all')
        )

        self.update_state(state='PROGRESS', meta={'current': 80, 'total': 100, 'status': 'Saving...'})

        output_filename = secure_filename(f"thickened_{os.path.basename(input_path)}")
        output_path = os.path.join(output_folder, output_filename)
        result['mesh'].export(output_path)

        return {
            'success': True,
            'download_url': f'/modeling/download/{output_filename}',
            'stats': result.get('stats', {})
        }
    except Exception as e:
        logger.error(f"Thicken task failed: {e}", exc_info=True)
        return {'success': False, 'error': str(e)}


@celery.task(bind=True, name='tasks.hollow_mesh')
def hollow_mesh_task(self, input_path, params, output_folder):
    """Hollow out mesh in background"""
    try:
        from programs.modeling.utils import hollow, mesh_utils
        import os
        from werkzeug.utils import secure_filename

        self.update_state(state='PROGRESS', meta={'current': 20, 'total': 100, 'status': 'Loading mesh...'})

        mesh = mesh_utils.load_stl(input_path)

        self.update_state(state='PROGRESS', meta={'current': 40, 'total': 100, 'status': 'Hollowing...'})

        result = hollow.hollow_mesh(
            mesh,
            wall_thickness=float(params.get('wall_thickness', 2.0)),
            drainage_hole_diameter=float(params.get('drainage_hole', 0)) if params.get('drainage_hole') else None
        )

        self.update_state(state='PROGRESS', meta={'current': 80, 'total': 100, 'status': 'Saving...'})

        output_filename = secure_filename(f"hollow_{os.path.basename(input_path)}")
        output_path = os.path.join(output_folder, output_filename)
        result['mesh'].export(output_path)

        return {
            'success': True,
            'download_url': f'/modeling/download/{output_filename}',
            'stats': result.get('stats', {})
        }
    except Exception as e:
        logger.error(f"Hollow task failed: {e}", exc_info=True)
        return {'success': False, 'error': str(e)}


@celery.task(bind=True, name='tasks.boolean_operation')
def boolean_operation_task(self, mesh1_path, mesh2_path, operation, output_folder):
    """Perform boolean operation in background"""
    try:
        from programs.modeling.utils import mesh_utils
        import os
        from werkzeug.utils import secure_filename

        self.update_state(state='PROGRESS', meta={'current': 20, 'total': 100, 'status': 'Loading meshes...'})

        mesh1 = mesh_utils.load_stl(mesh1_path)
        mesh2 = mesh_utils.load_stl(mesh2_path)

        self.update_state(state='PROGRESS', meta={'current': 50, 'total': 100, 'status': f'Performing {operation}...'})

        if operation == 'union':
            result_mesh = mesh1.union(mesh2)
        elif operation == 'difference':
            result_mesh = mesh1.difference(mesh2)
        elif operation == 'intersection':
            result_mesh = mesh1.intersection(mesh2)
        else:
            raise ValueError(f"Invalid operation: {operation}")

        self.update_state(state='PROGRESS', meta={'current': 80, 'total': 100, 'status': 'Saving...'})

        output_filename = secure_filename(f"boolean_{operation}_{os.path.basename(mesh1_path)}")
        output_path = os.path.join(output_folder, output_filename)
        result_mesh.export(output_path)

        return {
            'success': True,
            'download_url': f'/modeling/download/{output_filename}',
            'stats': {
                'operation': operation,
                'vertices': len(result_mesh.vertices),
                'faces': len(result_mesh.faces)
            }
        }
    except Exception as e:
        logger.error(f"Boolean task failed: {e}", exc_info=True)
        return {'success': False, 'error': str(e)}


# ============================================================================
# TASK STATUS UTILITIES
# ============================================================================

def get_task_status(task_id):
    """
    Get status of a background task.

    Args:
        task_id: Celery task ID

    Returns:
        dict: Task status information
    """
    task = celery.AsyncResult(task_id)

    if task.state == 'PENDING':
        return {
            'state': 'PENDING',
            'current': 0,
            'total': 100,
            'status': 'Task is waiting to start...'
        }
    elif task.state == 'PROGRESS':
        return {
            'state': 'PROGRESS',
            'current': task.info.get('current', 0),
            'total': task.info.get('total', 100),
            'status': task.info.get('status', 'Processing...')
        }
    elif task.state == 'SUCCESS':
        return {
            'state': 'SUCCESS',
            'current': 100,
            'total': 100,
            'status': 'Complete!',
            'result': task.result
        }
    elif task.state == 'FAILURE':
        return {
            'state': 'FAILURE',
            'current': 0,
            'total': 100,
            'status': 'Task failed',
            'error': str(task.info)
        }
    else:
        return {
            'state': task.state,
            'current': 0,
            'total': 100,
            'status': str(task.state)
        }
