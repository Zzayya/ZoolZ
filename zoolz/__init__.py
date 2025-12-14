"""
ZoolZ Core - Intelligent Program Orchestrator

This package contains the core logic for ZoolZ, which manages:
- Service orchestration (Redis, Celery, Flask)
- Program lifecycle (starting/stopping programs)
- Dependency management (auto-starting required services)
- Admin API (for Swift admin panel integration)
- File synchronization (for development workflow)
"""

__version__ = "1.0.0"
__author__ = "Isaiah Miro"

from .core import ZoolzOrchestrator
from .service_manager import ServiceManager
from .program_registry import ProgramRegistry

__all__ = ['ZoolzOrchestrator', 'ServiceManager', 'ProgramRegistry']
