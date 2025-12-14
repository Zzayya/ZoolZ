"""
Service Manager - Manages Redis, Celery, and other services

Handles starting/stopping services based on which programs are active.
"""

import subprocess
import os
import signal
import time
import logging
from typing import Dict, Optional, List

logger = logging.getLogger(__name__)


class ServiceManager:
    """
    Manages backend services (Redis, Celery, etc.)
    """

    def __init__(self):
        self.services: Dict[str, Dict] = {
            'redis': {
                'running': False,
                'pid': None,
                'port': 6379,
                'start_command': 'redis-server --daemonize yes --port 6379',
                'stop_command': 'redis-cli shutdown',
                'check_command': 'redis-cli ping',
            },
            'celery': {
                'running': False,
                'pid': None,
                'port': None,
                'start_command': 'celery -A tasks worker --loglevel=info --detach --pidfile=celery.pid',
                'stop_command': None,  # Will use PID
                'check_command': 'celery -A tasks inspect ping',
            }
        }

        # Track which programs are currently active
        self.active_programs: List[str] = []

    def is_service_running(self, service_name: str) -> bool:
        """
        Check if a service is currently running

        Args:
            service_name: Name of service ('redis' or 'celery')

        Returns:
            True if service is running
        """
        service = self.services.get(service_name)
        if not service:
            return False

        check_cmd = service.get('check_command')
        if not check_cmd:
            return False

        try:
            result = subprocess.run(
                check_cmd,
                shell=True,
                capture_output=True,
                timeout=2
            )

            # Redis returns "PONG"
            if service_name == 'redis':
                is_running = b'PONG' in result.stdout
            # Celery returns JSON with worker info
            elif service_name == 'celery':
                is_running = result.returncode == 0
            else:
                is_running = False

            self.services[service_name]['running'] = is_running
            return is_running

        except Exception as e:
            logger.error(f"Error checking {service_name}: {e}")
            return False

    def start_service(self, service_name: str) -> bool:
        """
        Start a service if not already running

        Args:
            service_name: Name of service to start

        Returns:
            True if service started successfully or already running
        """
        # Check if already running
        if self.is_service_running(service_name):
            logger.info(f"{service_name} already running")
            return True

        service = self.services.get(service_name)
        if not service:
            logger.error(f"Unknown service: {service_name}")
            return False

        start_cmd = service.get('start_command')
        if not start_cmd:
            logger.error(f"No start command for {service_name}")
            return False

        try:
            logger.info(f"Starting {service_name}...")
            result = subprocess.run(
                start_cmd,
                shell=True,
                capture_output=True,
                timeout=10
            )

            # Wait a moment for service to start
            time.sleep(1)

            # Verify it started
            if self.is_service_running(service_name):
                logger.info(f"✅ {service_name} started successfully")
                return True
            else:
                logger.error(f"Failed to start {service_name}")
                logger.error(f"Output: {result.stdout.decode()}")
                logger.error(f"Error: {result.stderr.decode()}")
                return False

        except Exception as e:
            logger.error(f"Error starting {service_name}: {e}")
            return False

    def stop_service(self, service_name: str, force: bool = False) -> bool:
        """
        Stop a service

        Args:
            service_name: Name of service to stop
            force: If True, force stop even if programs are using it

        Returns:
            True if service stopped successfully
        """
        if not force:
            # Don't stop if other programs need it
            from .program_registry import ProgramRegistry
            needed_services = ProgramRegistry.get_all_active_dependencies(self.active_programs)
            if service_name in needed_services:
                logger.warning(f"Cannot stop {service_name}: still needed by active programs")
                return False

        service = self.services.get(service_name)
        if not service:
            return False

        try:
            # Check if it's actually running first
            if not self.is_service_running(service_name):
                logger.info(f"{service_name} not running")
                return True

            logger.info(f"Stopping {service_name}...")

            # Use custom stop command if available
            stop_cmd = service.get('stop_command')
            if stop_cmd:
                subprocess.run(stop_cmd, shell=True, timeout=5)

            # Or kill by PID
            elif service.get('pid'):
                os.kill(service['pid'], signal.SIGTERM)

            # Or read PID from file (Celery)
            elif service_name == 'celery' and os.path.exists('celery.pid'):
                with open('celery.pid', 'r') as f:
                    pid = int(f.read().strip())
                    os.kill(pid, signal.SIGTERM)
                os.remove('celery.pid')

            # Wait for shutdown
            time.sleep(2)

            # Verify stopped
            if not self.is_service_running(service_name):
                logger.info(f"✅ {service_name} stopped successfully")
                self.services[service_name]['running'] = False
                self.services[service_name]['pid'] = None
                return True
            else:
                logger.warning(f"{service_name} may still be running")
                return False

        except Exception as e:
            logger.error(f"Error stopping {service_name}: {e}")
            return False

    def ensure_dependencies(self, program_id: str) -> bool:
        """
        Ensure all required services are running for a program

        Args:
            program_id: Program identifier

        Returns:
            True if all dependencies started successfully
        """
        from .program_registry import ProgramRegistry

        dependencies = ProgramRegistry.get_dependencies(program_id)

        if not dependencies:
            logger.info(f"Program {program_id} has no dependencies")
            return True

        logger.info(f"Ensuring dependencies for {program_id}: {dependencies}")

        # Start dependencies in order (Redis before Celery)
        for service in dependencies:
            if not self.start_service(service):
                logger.error(f"Failed to start dependency: {service}")
                return False

        return True

    def register_active_program(self, program_id: str):
        """
        Register that a program is now active

        This triggers starting of required services.

        Args:
            program_id: Program identifier
        """
        if program_id not in self.active_programs:
            logger.info(f"Activating program: {program_id}")
            self.active_programs.append(program_id)
            self.ensure_dependencies(program_id)

    def unregister_active_program(self, program_id: str):
        """
        Unregister an active program

        This may trigger cleanup of unused services.

        Args:
            program_id: Program identifier
        """
        if program_id in self.active_programs:
            logger.info(f"Deactivating program: {program_id}")
            self.active_programs.remove(program_id)
            self.cleanup_unused_services()

    def cleanup_unused_services(self):
        """
        Stop services that are no longer needed by any active program
        """
        from .program_registry import ProgramRegistry

        # Get all services still needed
        needed_services = ProgramRegistry.get_all_active_dependencies(self.active_programs)

        # Stop services that aren't needed
        for service_name in ['celery', 'redis']:
            if service_name not in needed_services:
                if self.is_service_running(service_name):
                    logger.info(f"Cleaning up unused service: {service_name}")
                    self.stop_service(service_name, force=True)

    def get_status(self) -> Dict:
        """
        Get status of all services

        Returns:
            Dict with service statuses
        """
        status = {}
        for service_name in self.services.keys():
            is_running = self.is_service_running(service_name)
            status[service_name] = {
                'running': is_running,
                'pid': self.services[service_name].get('pid'),
                'port': self.services[service_name].get('port'),
            }
        return status

    def stop_all(self):
        """Stop all services (for shutdown)"""
        logger.info("Stopping all services...")
        self.stop_service('celery', force=True)
        self.stop_service('redis', force=True)
