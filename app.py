#!/usr/bin/env python3
"""
ZoolZ - Flask Application
Multi-Purpose 3D Design Tool - Main entry point with HUB navigation
"""

from flask import Flask, render_template, jsonify
from blueprints.parametric_cad import parametric_bp
from blueprints.cookie_cutter import cookie_bp
from blueprints.people_finder import people_finder_bp
from blueprints.digital_footprint import digital_footprint_bp
from config import config
import os

app = Flask(__name__)

# Load configuration
config_name = os.environ.get('FLASK_ENV', 'development')
app.config.from_object(config[config_name])

# Ensure folders exist
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
os.makedirs(app.config['OUTPUT_FOLDER'], exist_ok=True)
os.makedirs(app.config['DATABASE_FOLDER'], exist_ok=True)

# Register blueprints
app.register_blueprint(parametric_bp, url_prefix='/parametric')
app.register_blueprint(cookie_bp, url_prefix='/cookie')
app.register_blueprint(people_finder_bp, url_prefix='/people')
app.register_blueprint(digital_footprint_bp, url_prefix='/footprint')


@app.route('/')
def index():
    """Main HUB page with mode selection"""
    return render_template('hub.html')


@app.route('/api/health')
def health_check():
    """Simple health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'version': '1.0.0'
    })


if __name__ == '__main__':
    app.run(debug=app.config['DEBUG'], host='0.0.0.0', port=5001)
