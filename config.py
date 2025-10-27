#!/usr/bin/env python3
"""
Application Configuration
Centralized settings for 3D Modulator Flask app
"""

import os


class Config:
    """Base configuration"""

    # Flask settings
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-secret-key-change-in-production'
    DEBUG = True

    # File upload settings
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB max upload
    ALLOWED_IMAGE_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'bmp', 'webp'}

    # Directory settings
    BASE_DIR = os.path.abspath(os.path.dirname(__file__))
    UPLOAD_FOLDER = os.path.join(BASE_DIR, 'uploads')
    OUTPUT_FOLDER = os.path.join(BASE_DIR, 'outputs')

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
        'max_dim': (30.0, 200.0)
    }


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
