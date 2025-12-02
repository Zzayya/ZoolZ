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
import os
import json
from datetime import datetime
import hashlib

app = Flask(__name__)

# Load configuration
config_name = os.getenv('FLASK_ENV', 'development')
app.config.from_object(config[config_name])

# Ensure folders exist
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
os.makedirs(app.config['OUTPUT_FOLDER'], exist_ok=True)
os.makedirs(app.config['DATABASE_FOLDER'], exist_ok=True)

# Register blueprints
app.register_blueprint(parametric_bp, url_prefix='/parametric')
app.register_blueprint(modeling_bp, url_prefix='/modeling')
app.register_blueprint(people_finder_bp, url_prefix='/people_finder')
app.register_blueprint(digital_footprint_bp, url_prefix='/footprint')


# ============================================================================
# USER MANAGEMENT FUNCTIONS
# ============================================================================

USERS_FILE = os.path.join(app.config['DATABASE_FOLDER'], 'users.json')


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
    """Hash password with SHA-256"""
    return hashlib.sha256(password.encode()).hexdigest()


def verify_password(password, hashed):
    """Verify password against hash"""
    return hash_password(password) == hashed


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

    return jsonify({
        'success': True,
        'message': f"Welcome back, {user['name']}!",
        'user': session['user']
    })


@app.route('/api/logout', methods=['POST'])
def api_logout():
    """Logout endpoint - clears session"""
    session.clear()
    return jsonify({'success': True, 'message': 'Logged out'})


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
def health_check():
    """Simple health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'version': '1.0.0',
        'authenticated': session.get('authenticated', False)
    })


if __name__ == '__main__':
    app.run(debug=app.config['DEBUG'], host='0.0.0.0', port=5001)
