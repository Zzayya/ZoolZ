"""
ZoolZmstr - Zoolz Master Control Logic

This package contains the brain/logic for Zoolz itself.
Handles server detection, folder management, program launching, and coordination.
"""

from .detection import is_server, get_environment
from .folder_manager import setup_server_folders, get_data_paths
from .process_manager import process_manager, ProgramRequirements
from .health_monitor import health_monitor

__all__ = [
    'is_server',
    'get_environment',
    'setup_server_folders',
    'get_data_paths',
    'process_manager',
    'ProgramRequirements',
    'health_monitor'
]
