"""
ZoolZ Core Orchestrator

Main orchestration logic that manages programs and their services.
"""

import logging
from typing import Dict, List, Optional
from .service_manager import ServiceManager
from .program_registry import ProgramRegistry

logger = logging.getLogger(__name__)


class ZoolzOrchestrator:
    """
    Main Zoolz orchestrator - manages programs and their dependencies

    This is the brain of Zoolz that:
    - Tracks which programs are active
    - Starts/stops services as needed
    - Handles program lifecycle
    - Provides status information
    """

    _instance: Optional['ZoolzOrchestrator'] = None

    def __new__(cls):
        """Singleton pattern - only one orchestrator instance"""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        """Initialize the orchestrator"""
        if self._initialized:
            return

        self.service_manager = ServiceManager()
        self.program_registry = ProgramRegistry
        self._initialized = True

        logger.info("ZoolZ Orchestrator initialized")

    def on_program_access(self, program_id: str):
        """
        Called when a user accesses a program

        This triggers starting of required services.

        Args:
            program_id: Program identifier (e.g., 'modeling')
        """
        logger.info(f"Program accessed: {program_id}")

        # Register program as active
        self.service_manager.register_active_program(program_id)

        # Get dependencies
        deps = self.program_registry.get_dependencies(program_id)

        if deps:
            logger.info(f"Program {program_id} requires: {deps}")
        else:
            logger.info(f"Program {program_id} has no service dependencies")

    def on_program_close(self, program_id: str):
        """
        Called when a user closes/leaves a program

        This may trigger cleanup of unused services.

        Args:
            program_id: Program identifier
        """
        logger.info(f"Program closed: {program_id}")

        # Unregister program
        self.service_manager.unregister_active_program(program_id)

    def get_status(self) -> Dict:
        """
        Get complete status of Zoolz system

        Returns:
            Dict with:
            - services: Status of all services
            - programs: Status of all programs
            - active_programs: List of currently active programs
        """
        service_status = self.service_manager.get_status()

        program_status = {}
        for program_id in self.program_registry.get_all_programs():
            info = self.program_registry.get_program_info(program_id)
            program_status[program_id] = {
                'name': info.get('name'),
                'active': program_id in self.service_manager.active_programs,
                'dependencies': self.program_registry.get_dependencies(program_id),
                'heavy_processing': info.get('heavy_processing', False),
            }

        return {
            'services': service_status,
            'programs': program_status,
            'active_programs': self.service_manager.active_programs,
        }

    def start_service(self, service_name: str) -> bool:
        """Manually start a service (for admin panel)"""
        return self.service_manager.start_service(service_name)

    def stop_service(self, service_name: str, force: bool = False) -> bool:
        """Manually stop a service (for admin panel)"""
        return self.service_manager.stop_service(service_name, force)

    def restart_program(self, program_id: str) -> bool:
        """
        Restart a specific program (reload its blueprint)

        Note: This doesn't restart Flask, just reloads the program's logic.

        Args:
            program_id: Program to restart

        Returns:
            True if successful
        """
        logger.info(f"Restarting program: {program_id}")

        # For now, just restart its services
        # In the future, we could reload the blueprint module
        deps = self.program_registry.get_dependencies(program_id)

        success = True
        for service in deps:
            if not self.service_manager.stop_service(service, force=True):
                success = False
            if not self.service_manager.start_service(service):
                success = False

        return success

    def shutdown(self):
        """
        Gracefully shutdown Zoolz and all services
        """
        logger.info("Shutting down ZoolZ...")

        # Clear active programs
        self.service_manager.active_programs.clear()

        # Stop all services
        self.service_manager.stop_all()

        logger.info("ZoolZ shutdown complete")


# Global orchestrator instance
orchestrator = ZoolzOrchestrator()
