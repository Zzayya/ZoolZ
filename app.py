#!/usr/bin/env python3
"""
ZoolZ - Flask Application
Multi-Purpose 3D Design Tool - Main entry point with HUB navigation
"""

from flask import Flask, render_template, jsonify, session, redirect, url_for, request
from programs.ParametricCAD.blueprint import parametric_bp
from programs.Modeling.blueprint import modeling_bp
from programs.PeopleFinder.blueprint import people_finder_bp
from programs.DigitalFootprint.blueprint import digital_footprint_bp
from decorators import login_required, admin_required
from config import config
from rate_limit import limiter
import os
import json
import logging
from datetime import datetime
import atexit
from werkzeug.security import generate_password_hash, check_password_hash
from zoolz.brain import generate_zoolz_reply

logger = logging.getLogger(__name__)

# ZoolZmstr - Zoolz Master Control Logic
from zoolz.ZoolZmstr import (
    is_server,
    get_environment,
    setup_server_folders,
    process_manager,
    health_monitor
)

app = Flask(__name__)

# Load configuration
config_name = os.getenv('FLASK_ENV', 'development')
app.config.from_object(config[config_name])

# Initialize rate limiter
limiter.init_app(app)

# ============================================================================
# ZOOLZ MASTER INITIALIZATION
# ============================================================================

# If running on server, set up ZoolZData folder structure
if is_server():
    print("\n" + "=" * 60)
    print("🖥️  ZOOLZ RUNNING ON SERVER")
    print("=" * 60)
    setup_server_folders(verbose=True)

    # Log server startup
    health_monitor.log('STARTUP', 'Zoolz server initialized')
    health_monitor.log_system_stats()
else:
    print("\n💻 Zoolz running on laptop (development mode)")

print(f"📍 Environment: {get_environment()}")
print(f"📂 Data root: {app.config['DATABASE_FOLDER']}")
print()

# Ensure folders exist (works for both server and laptop)
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
os.makedirs(app.config['OUTPUT_FOLDER'], exist_ok=True)
os.makedirs(app.config['DATABASE_FOLDER'], exist_ok=True)

# Register cleanup handler for processes
atexit.register(process_manager.cleanup_all)

# Register blueprints
app.register_blueprint(parametric_bp, url_prefix='/parametric')
app.register_blueprint(modeling_bp, url_prefix='/modeling')
app.register_blueprint(people_finder_bp, url_prefix='/people_finder')
app.register_blueprint(digital_footprint_bp, url_prefix='/footprint')


# ============================================================================
# SMART PROCESS MANAGEMENT
# ============================================================================

# Track which programs are currently accessed
_program_url_map = {
    '/modeling': 'Modeling',
    '/parametric': 'ParametricCAD',
    '/people_finder': 'PeopleFinder',
    '/footprint': 'DigitalFootprint'
}

@app.before_request
def manage_program_processes():
    """
    Before each request, check if accessing a program and start required processes.
    This is Zoolz's brain - it knows what each program needs and boots it up automatically.
    """
    # Only manage processes for program routes
    for url_prefix, program_name in _program_url_map.items():
        if request.path.startswith(url_prefix):
            # User is accessing this program
            # Check if we've already started processes for this session
            session_key = f'_processes_started_{program_name}'

            if not session.get(session_key):
                # First access to this program in this session
                results = process_manager.program_accessed(program_name)

                # Log what happened
                for process_name, status in results.items():
                    if status == 'started':
                        app.logger.info(f"🚀 Started {process_name} for {program_name}")
                        health_monitor.log_process_start(process_name)
                    elif status == 'failed':
                        app.logger.warning(f"⚠️  Failed to start {process_name} for {program_name}")
                        health_monitor.log_error('PROCESS_START', f'Failed to start {process_name}')

                # Log program access
                health_monitor.log_program_access(program_name)

                # Mark that we've started processes for this program
                session[session_key] = True

            break


# ============================================================================
# CSRF PROTECTION (session-based)
# ============================================================================

def _generate_csrf_token():
    import secrets
    token = secrets.token_hex(16)
    session['csrf_token'] = token
    return token


@app.before_request
def enforce_csrf():
    """
    Simple double-submit CSRF: for authenticated sessions, require the session
    token to match either the X-CSRFToken header or XSRF-TOKEN cookie on
    unsafe methods. Exempt safe/unauthenticated or specific routes.
    """
    # Only enforce for authenticated sessions
    if not session.get('authenticated'):
        return

    # Safe methods
    if request.method in ('GET', 'HEAD', 'OPTIONS'):
        return

    # Exemptions
    csrf_exempt_paths = {
        '/api/auth/login',
        '/api/logout',
        '/api/health',
    }
    if any(request.path.startswith(p) for p in csrf_exempt_paths):
        return

    session_token = session.get('csrf_token')
    header_token = request.headers.get('X-CSRFToken') or request.headers.get('X-CSRF-Token')
    cookie_token = request.cookies.get('XSRF-TOKEN')
    provided = header_token or cookie_token

    if not session_token or not provided or session_token != provided:
        return jsonify({'error': 'CSRF token missing or invalid'}), 400


@app.after_request
def set_csrf_cookie(response):
    """
    Mirror the session CSRF token into a readable cookie for double-submit.
    """
    if session.get('authenticated'):
        token = session.get('csrf_token') or _generate_csrf_token()
        response.set_cookie('XSRF-TOKEN', token, samesite='Lax')
    return response


# ============================================================================
# USER MANAGEMENT FUNCTIONS
# ============================================================================

USERS_FILE = os.path.join(app.config['DATABASE_FOLDER'], 'users.json')


def ensure_users_file_permissions():
    """
    Set secure permissions on users.json (owner read/write only).

    Sets file permissions to 0o600 (rw-------) on Unix/Linux/macOS to prevent
    other users from reading password hashes. On Windows or if permissions
    cannot be set, this function silently fails to avoid breaking startup.

    This is a security measure to protect sensitive user data.
    """
    if os.path.exists(USERS_FILE):
        try:
            # Unix/Linux/macOS: 600 (owner read/write only)
            os.chmod(USERS_FILE, 0o600)
            logger.info(f"Set secure permissions on {USERS_FILE}")
        except (OSError, NotImplementedError) as e:
            # Windows or permission denied - don't crash, just log
            logger.warning(f"Could not set file permissions on {USERS_FILE}: {e}")
            pass


def load_users():
    """Load users from JSON file"""
    if not os.path.exists(USERS_FILE):
        return {"users": {}, "nextUserNumber": 100001}
    with open(USERS_FILE, 'r') as f:
        return json.load(f)


def save_users(data):
    """Save users to JSON file"""
    with open(USERS_FILE, 'w') as f:
        json.dump(data, f, indent=2)


def hash_password(password):
    """Hash password using werkzeug's salted PBKDF2."""
    return generate_password_hash(password)


def verify_password(password, hashed):
    """Verify password against hash (supports legacy SHA-256)."""
    if hashed.startswith('pbkdf2:'):
        return check_password_hash(hashed, password)
    # Legacy SHA-256 support
    import hashlib
    return hashlib.sha256(password.encode()).hexdigest() == hashed


def generate_user_number():
    """Generate next sequential user number"""
    data = load_users()
    user_number = str(data.get('nextUserNumber', 100001))
    data['nextUserNumber'] = int(user_number) + 1
    save_users(data)
    return user_number


def create_user(username, full_name, password, role='user'):
    """Create a new user"""
    data = load_users()

    # Check if username exists
    if username.lower() in data['users']:
        return None, "Username already exists"

    # Generate user number
    user_number = generate_user_number()

    # Create user
    user = {
        "name": username,
        "fullName": full_name,
        "userNumber": user_number,
        "passwordHash": hash_password(password),
        "role": role,
        "createdAt": datetime.utcnow().isoformat() + 'Z',
        "lastLogin": None
    }

    data['users'][username.lower()] = user
    save_users(data)

    return user, None


def authenticate_user(username, password):
    """Authenticate user with username and password"""
    data = load_users()
    user = data['users'].get(username.lower())

    if not user:
        return None, "User not found"

    if not verify_password(password, user['passwordHash']):
        return None, "Invalid password"

    # Upgrade legacy hashes to salted hashes transparently
    if not user['passwordHash'].startswith('pbkdf2:'):
        user['passwordHash'] = hash_password(password)

    # Update last login
    user['lastLogin'] = datetime.utcnow().isoformat() + 'Z'
    data['users'][username.lower()] = user
    save_users(data)

    return user, None


def update_last_login(username):
    """Update user's last login timestamp"""
    data = load_users()
    if username.lower() in data['users']:
        data['users'][username.lower()]['lastLogin'] = datetime.utcnow().isoformat() + 'Z'
        save_users(data)


# ============================================================================
# ROUTES
# ============================================================================

@app.route('/')
def index():
    """Login page - gateway to ZoolZ Hub"""
    # Redirect to hub if already authenticated
    if session.get('authenticated'):
        return redirect(url_for('hub'))
    return render_template('login.html')


@app.route('/hub')
@login_required
def hub():
    """Main HUB page with mode selection (requires auth)"""
    user = session.get('user')
    return render_template('hub.html', user=user)


@app.route('/api/auth/login', methods=['POST'])
def api_login():
    """Login endpoint - authenticates with username and password"""
    data = request.get_json()
    username = data.get('username', '').strip()
    password = data.get('password', '').strip()

    if not username or not password:
        return jsonify({'success': False, 'message': 'Username and password required'}), 400

    # Authenticate user
    user, error = authenticate_user(username, password)

    if error:
        return jsonify({'success': False, 'message': error}), 401

    # Set session
    session['authenticated'] = True
    session['user'] = {
        'name': user['name'],
        'fullName': user['fullName'],
        'userNumber': user['userNumber'],
        'role': user['role']
    }

    # Issue CSRF token
    csrf_token = session.get('csrf_token') or _generate_csrf_token()

    resp = jsonify({
        'success': True,
        'message': f"Welcome back, {user['name']}!",
        'user': session['user']
    })
    resp.set_cookie('XSRF-TOKEN', csrf_token, samesite='Lax')
    return resp


@app.route('/api/logout', methods=['POST'])
def api_logout():
    """Logout endpoint - clears session"""
    session.clear()
    resp = jsonify({'success': True, 'message': 'Logged out'})
    resp.set_cookie('XSRF-TOKEN', '', expires=0)
    return resp


@app.route('/api/auth/user', methods=['GET'])
@login_required
def get_current_user():
    """Get current logged-in user info"""
    return jsonify({
        'success': True,
        'user': session.get('user')
    })


@app.route('/api/admin/users', methods=['GET'])
@admin_required
def list_users():
    """List all users (admin only)"""
    data = load_users()
    users_list = []
    for username, user in data['users'].items():
        users_list.append({
            'name': user['name'],
            'fullName': user['fullName'],
            'userNumber': user['userNumber'],
            'role': user['role'],
            'createdAt': user['createdAt'],
            'lastLogin': user['lastLogin']
        })
    return jsonify({'success': True, 'users': users_list})


@app.route('/api/admin/users/create', methods=['POST'])
@admin_required
def admin_create_user():
    """Create a new user (admin only)"""
    data = request.get_json()
    username = data.get('username', '').strip()
    full_name = data.get('fullName', '').strip()
    password = data.get('password', '').strip()
    role = data.get('role', 'user')

    if not username or not full_name or not password:
        return jsonify({'success': False, 'message': 'All fields required'}), 400

    user, error = create_user(username, full_name, password, role)

    if error:
        return jsonify({'success': False, 'message': error}), 400

    return jsonify({
        'success': True,
        'message': f'User {username} created successfully',
        'user': {
            'name': user['name'],
            'fullName': user['fullName'],
            'userNumber': user['userNumber'],
            'role': user['role']
        }
    })


@app.route('/api/health')
@limiter.exempt
def health_check():
    """
    Server health check endpoint.

    Returns system stats, uptime, process status, and any warnings.
    Useful for monitoring when running on server.
    """
    health_data = health_monitor.check_health()
    process_status = process_manager.get_status()

    return jsonify({
        'status': health_data['status'],
        'version': '1.0.0',
        'environment': get_environment(),
        'authenticated': session.get('authenticated', False),
        'uptime_hours': round(health_data.get('uptime_hours', 0), 2),
        'system': {
            'cpu_percent': health_data['stats'].get('cpu_percent', 0),
            'memory_percent': health_data['stats'].get('memory_percent', 0),
            'memory_available_gb': round(health_data['stats'].get('memory_available_gb', 0), 1),
            'disk_percent': health_data['stats'].get('disk_percent', 0),
            'disk_free_gb': round(health_data['stats'].get('disk_free_gb', 0), 1)
        },
        'warnings': health_data.get('warnings', []),
        'active_programs': process_status.get('active_programs', []),
        'running_processes': list(process_status.get('running_processes', {}).keys())
    })


@app.route('/api/zoolz/chat', methods=['POST'])
@login_required
def zoolz_chat():
    """
    Lightweight local chat endpoint (no external AI calls).
    Logs interactions to JEFF for summaries.
    """
    data = request.get_json(silent=True) or {}
    message = (data.get('message') or '').strip()
    if not message:
        return jsonify({'success': False, 'reply': "Type something to chat."}), 400

    user = session.get('user', {}).get('name', 'unknown')
    reply = generate_zoolz_reply(message, status_fetcher=process_manager.get_status, user=user)
    return jsonify({'success': True, **reply})


if __name__ == '__main__':
    # Security: Set secure permissions on users.json
    ensure_users_file_permissions()

    port = int(os.getenv('PORT', 5001))
    app.run(debug=app.config['DEBUG'], host='0.0.0.0', port=port)
