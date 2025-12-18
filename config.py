#!/usr/bin/env python3
"""
Application Configuration
Centralized settings for 3D Modulator Flask app
"""

import os
from dotenv import load_dotenv
from zoolz.ZoolZmstr import get_data_paths

# Load environment variables from .env file
load_dotenv()


class Config:
    """Base configuration"""

    # Flask settings
    SECRET_KEY = os.getenv('SECRET_KEY')
    if not SECRET_KEY or SECRET_KEY == 'dev-secret-key-change-in-production':
        raise RuntimeError(
            "SECRET_KEY missing. Run setup to create .env with a strong SECRET_KEY."
        )
    DEBUG = os.getenv('DEBUG', 'True').lower() == 'true'

    # File upload settings
    MAX_CONTENT_LENGTH = int(os.getenv('MAX_CONTENT_LENGTH', 104857600))  # Default 100MB
    ALLOWED_IMAGE_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'bmp', 'webp'}

    # Directory settings - NOW USING ZOOLZMSTR FOR SERVER/LAPTOP DETECTION
    BASE_DIR = os.path.abspath(os.path.dirname(__file__))

    # Get environment-aware paths from ZoolZmstr
    _data_paths = get_data_paths()

    UPLOAD_FOLDER = os.getenv('UPLOAD_FOLDER', str(_data_paths['uploads']))
    OUTPUT_FOLDER = os.getenv('OUTPUT_FOLDER', str(_data_paths['outputs']))
    DATABASE_FOLDER = os.getenv('DATABASE_FOLDER', str(_data_paths['database']))
    MY_MODELS_FOLDER = os.getenv('MY_MODELS_FOLDER', str(_data_paths['modeling_saves']))

    # Cookie cutter defaults
    COOKIE_CUTTER_DEFAULTS = {
        'blade_thick': 2.0,
        'blade_height': 20.0,
        'base_thick': 3.0,
        'base_extra': 10.0,
        'max_dim': 90.0,
        'no_base': False
    }

    # Cookie cutter constraints (for validation)
    COOKIE_CUTTER_CONSTRAINTS = {
        'blade_thick': (0.5, 5.0),     # min, max in mm
        'blade_height': (10.0, 50.0),
        'base_thick': (1.0, 10.0),
        'base_extra': (5.0, 30.0),
        'max_dim': (30.0, 200.0),
        'detail_level': (0.0, 1.0)     # 0.0 = smooth, 1.0 = detailed
    }

    # Parametric CAD defaults
    PARAMETRIC_CAD_DEFAULTS = {
        'box': {
            'width': 20.0,
            'height': 20.0,
            'depth': 20.0,
            'center': True
        },
        'cylinder': {
            'radius': 10.0,
            'height': 20.0,
            'segments': 32,
            'center': True
        },
        'sphere': {
            'radius': 10.0,
            'subdivisions': 3
        },
        'cone': {
            'radius': 10.0,
            'height': 20.0,
            'segments': 32,
            'center': True
        },
        'torus': {
            'major_radius': 15.0,
            'minor_radius': 5.0,
            'major_sections': 32,
            'minor_sections': 16
        },
        'prism': {
            'sides': 6,
            'radius': 10.0,
            'height': 20.0
        }
    }

    # Parametric CAD constraints (for validation)
    PARAMETRIC_CAD_CONSTRAINTS = {
        'dimension': (0.1, 500.0),     # General dimension limits (mm)
        'radius': (0.1, 200.0),        # Radius limits (mm)
        'height': (0.1, 500.0),        # Height limits (mm)
        'segments': (3, 256),          # Resolution segments
        'subdivisions': (1, 6),        # Sphere subdivisions
        'sides': (3, 20)               # Prism sides
    }

    # People Finder settings
    PEOPLE_FINDER_DB = os.path.join(str(_data_paths['database']), 'search_cache.db')
    PEOPLE_FINDER_CACHE_HOURS = int(os.getenv('PEOPLE_FINDER_CACHE_HOURS', 24))

    # People Finder API keys (optional - set via environment variables)
    GOOGLE_API_KEY = os.getenv('GOOGLE_API_KEY')  # Google Custom Search (100 free queries/day)
    GOOGLE_SEARCH_ENGINE_ID = os.getenv('GOOGLE_SEARCH_ENGINE_ID')
    NUMVERIFY_API_KEY = os.getenv('NUMVERIFY_API_KEY')  # NumVerify phone validation (250 free/month)

    # Database URL (for future SQLAlchemy support)
    DATABASE_URL = os.getenv('DATABASE_URL', 'sqlite:///zoolz.db')

    # Redis/Celery settings (for background tasks)
    REDIS_URL = os.getenv('REDIS_URL', 'redis://localhost:6379/0')
    CELERY_BROKER_URL = os.getenv('CELERY_BROKER_URL', 'redis://localhost:6379/0')
    CELERY_RESULT_BACKEND = os.getenv('CELERY_RESULT_BACKEND', 'redis://localhost:6379/0')

    # Mesh processing constraints
    MAX_MESH_VERTICES = int(os.getenv('MAX_MESH_VERTICES', 10000000))
    MAX_MESH_FACES = int(os.getenv('MAX_MESH_FACES', 20000000))
    MAX_BOOLEAN_OPERATIONS = int(os.getenv('MAX_BOOLEAN_OPERATIONS', 10))


class DevelopmentConfig(Config):
    """Development configuration"""
    DEBUG = True


class ProductionConfig(Config):
    """Production configuration"""
    DEBUG = False
    SECRET_KEY = os.environ.get('SECRET_KEY')  # Must be set in production


# Configuration dictionary
config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig
}
