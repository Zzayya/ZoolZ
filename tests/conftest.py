#!/usr/bin/env python3
"""
Pytest Configuration
Fixtures and setup for all tests
"""

import pytest
import sys
import os
import tempfile
import shutil

# Add parent directory to path so tests can import from ZoolZ
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))


@pytest.fixture(scope='session')
def app():
    """Create Flask app for testing"""
    from flask import Flask
    from programs.modeling.blueprint import modeling_bp
    from config import config

    app = Flask(__name__)
    app.config.from_object(config['development'])
    app.config['TESTING'] = True

    # Use temporary folders for testing
    app.config['UPLOAD_FOLDER'] = tempfile.mkdtemp()
    app.config['OUTPUT_FOLDER'] = tempfile.mkdtemp()

    app.register_blueprint(modeling_bp, url_prefix='/modeling')

    yield app

    # Cleanup temporary folders
    shutil.rmtree(app.config['UPLOAD_FOLDER'], ignore_errors=True)
    shutil.rmtree(app.config['OUTPUT_FOLDER'], ignore_errors=True)


@pytest.fixture
def client(app):
    """Create test client"""
    return app.test_client()


@pytest.fixture
def temp_dir():
    """Create temporary directory for test files"""
    temp = tempfile.mkdtemp()
    yield temp
    shutil.rmtree(temp, ignore_errors=True)


@pytest.fixture
def sample_cube_mesh():
    """Create a simple cube mesh for testing"""
    import trimesh
    return trimesh.creation.box(extents=[10, 10, 10])


@pytest.fixture
def sample_sphere_mesh():
    """Create a simple sphere mesh for testing"""
    import trimesh
    return trimesh.creation.icosphere(subdivisions=2, radius=5.0)


@pytest.fixture
def sample_stl_file(temp_dir, sample_cube_mesh):
    """Save a cube mesh as STL file"""
    import os
    filepath = os.path.join(temp_dir, 'test_cube.stl')
    sample_cube_mesh.export(filepath)
    return filepath
