"""
Admin API - REST endpoints for Swift admin panel

Provides endpoints for the Swift admin panel to:
- Start/stop/restart Zoolz and services
- Get status information
- View logs
- Restart individual programs
"""

from flask import Blueprint, jsonify, request
import subprocess
import os
import sys
import logging
from datetime import datetime
from .core import orchestrator

logger = logging.getLogger(__name__)

admin_bp = Blueprint('admin', __name__, url_prefix='/api/admin')


@admin_bp.route('/status', methods=['GET'])
def get_status():
    """
    Get complete status of Zoolz system

    Returns:
        JSON with services, programs, and system info
    """
    status = orchestrator.get_status()

    # Add system info
    status['system'] = {
        'python_version': sys.version,
        'flask_running': True,
        'pid': os.getpid(),
        'cwd': os.getcwd(),
        'timestamp': datetime.utcnow().isoformat() + 'Z',
    }

    return jsonify(status)


@admin_bp.route('/service/<service_name>/start', methods=['POST'])
def start_service(service_name):
    """
    Start a specific service

    Args:
        service_name: 'redis' or 'celery'
    """
    if service_name not in ['redis', 'celery']:
        return jsonify({'error': 'Invalid service name'}), 400

    success = orchestrator.start_service(service_name)

    return jsonify({
        'success': success,
        'service': service_name,
        'action': 'start'
    })


@admin_bp.route('/service/<service_name>/stop', methods=['POST'])
def stop_service(service_name):
    """
    Stop a specific service

    Args:
        service_name: 'redis' or 'celery'
    """
    if service_name not in ['redis', 'celery']:
        return jsonify({'error': 'Invalid service name'}), 400

    force = request.json.get('force', False) if request.json else False
    success = orchestrator.stop_service(service_name, force=force)

    return jsonify({
        'success': success,
        'service': service_name,
        'action': 'stop'
    })


@admin_bp.route('/service/<service_name>/restart', methods=['POST'])
def restart_service(service_name):
    """
    Restart a specific service

    Args:
        service_name: 'redis' or 'celery'
    """
    if service_name not in ['redis', 'celery']:
        return jsonify({'error': 'Invalid service name'}), 400

    # Stop then start
    orchestrator.stop_service(service_name, force=True)
    success = orchestrator.start_service(service_name)

    return jsonify({
        'success': success,
        'service': service_name,
        'action': 'restart'
    })


@admin_bp.route('/program/<program_id>/restart', methods=['POST'])
def restart_program(program_id):
    """
    Restart a specific program (reloads its services)

    Args:
        program_id: Program to restart
    """
    success = orchestrator.restart_program(program_id)

    return jsonify({
        'success': success,
        'program': program_id,
        'action': 'restart'
    })


@admin_bp.route('/restart', methods=['POST'])
def restart_flask():
    """
    Restart Flask application

    Note: This will kill the current process, so the admin panel
    needs to handle reconnection after a few seconds.
    """
    def restart_app():
        import time
        time.sleep(1)
        os.execv(sys.executable, [sys.executable] + sys.argv)

    from threading import Thread
    Thread(target=restart_app).start()

    return jsonify({
        'success': True,
        'message': 'Flask restarting...',
        'action': 'restart'
    })


@admin_bp.route('/shutdown', methods=['POST'])
def shutdown():
    """
    Gracefully shutdown Zoolz and all services
    """
    orchestrator.shutdown()

    def shutdown_app():
        import time
        time.sleep(1)
        os.kill(os.getpid(), 15)  # SIGTERM

    from threading import Thread
    Thread(target=shutdown_app).start()

    return jsonify({
        'success': True,
        'message': 'ZoolZ shutting down...',
        'action': 'shutdown'
    })


@admin_bp.route('/logs/<service_name>', methods=['GET'])
def get_logs(service_name):
    """
    Get recent logs for a service

    Args:
        service_name: 'flask', 'redis', or 'celery'
    """
    lines = request.args.get('lines', 100, type=int)

    log_files = {
        'flask': 'flask.log',
        'redis': '/usr/local/var/log/redis.log',  # Mac default
        'celery': 'celery.log',
    }

    log_file = log_files.get(service_name)
    if not log_file or not os.path.exists(log_file):
        return jsonify({
            'error': f'Log file not found for {service_name}'
        }), 404

    try:
        result = subprocess.run(
            f'tail -n {lines} {log_file}',
            shell=True,
            capture_output=True,
            text=True,
            timeout=5
        )

        return jsonify({
            'service': service_name,
            'lines': result.stdout.split('\n'),
            'file': log_file
        })
    except Exception as e:
        return jsonify({
            'error': str(e)
        }), 500


@admin_bp.route('/health', methods=['GET'])
def health_check():
    """
    Simple health check endpoint
    """
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.utcnow().isoformat() + 'Z'
    })
