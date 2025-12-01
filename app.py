#!/usr/bin/env python3
"""
ZoolZ - Flask Application
Multi-Purpose 3D Design Tool - Main entry point with HUB navigation
"""

from flask import Flask, render_template, jsonify, session, redirect, url_for
from blueprints.parametric_cad import parametric_bp
from programs.Modeling.blueprint import modeling_bp
from blueprints.people_finder import people_finder_bp
from blueprints.digital_footprint import digital_footprint_bp
from config import config
import os

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


@app.route('/')
def index():
    """Login page - gateway to ZoolZ Hub"""
    # Redirect to hub if already authenticated
    if session.get('authenticated'):
        return redirect(url_for('hub'))
    return render_template('login.html')


@app.route('/hub')
def hub():
    """Main HUB page with mode selection (requires auth)"""
    if not session.get('authenticated'):
        return redirect(url_for('index'))
    return render_template('hub.html')


@app.route('/api/auth/login', methods=['POST'])
def api_login():
    """Login endpoint - sets Flask session"""
    from flask import request
    data = request.get_json()
    passkey = data.get('passkey')
    user = data.get('user')

    # Simple passkey check (frontend already validated)
    if passkey == '442767' and user:
        session['authenticated'] = True
        session['user'] = user
        return jsonify({'success': True, 'message': f"Welcome, {user.get('name')}"})

    return jsonify({'success': False, 'message': 'Invalid credentials'}), 401


@app.route('/api/logout', methods=['POST'])
def api_logout():
    """Logout endpoint - clears session"""
    session.clear()
    return jsonify({'success': True, 'message': 'Logged out'})


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
