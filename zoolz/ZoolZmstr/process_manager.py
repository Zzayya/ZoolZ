"""
Process Manager - Smart Resource Management

Manages what processes/services need to run for each program.
Boots up dependencies only when needed, shuts them down when not in use.

Example:
- User opens Modeling → Start Redis + Celery
- User closes Modeling → Stop Redis + Celery (if no one else using them)
- User opens PeopleFinder → Start whatever PeopleFinder needs

This saves server resources and allows each program to have unique dependencies.
"""

import subprocess
import time
import signal
from typing import Dict, List, Optional, Set
from pathlib import Path
import psutil


class ProcessInfo:
    """Information about a running process."""

    def __init__(self, name: str, pid: int, command: str):
        self.name = name
        self.pid = pid
        self.command = command
        self.started_at = time.time()

    def is_running(self) -> bool:
        """Check if process is still running."""
        try:
            process = psutil.Process(self.pid)
            return process.is_running()
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            return False

    def stop(self) -> bool:
        """Stop the process gracefully."""
        try:
            process = psutil.Process(self.pid)
            process.terminate()  # Send SIGTERM
            process.wait(timeout=5)  # Wait up to 5 seconds
            return True
        except psutil.TimeoutExpired:
            # Force kill if didn't terminate
            try:
                process.kill()  # Send SIGKILL
                return True
            except:
                return False
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            return False


class ProgramRequirements:
    """Defines what processes/services a program needs to run."""

    def __init__(self, name: str):
        self.name = name
        self.requires: List[str] = []  # List of required process names
        self.optional: List[str] = []  # List of optional process names
        self.start_commands: Dict[str, str] = {}  # process_name -> start command
        self.stop_commands: Dict[str, str] = {}  # process_name -> stop command
        self.check_commands: Dict[str, str] = {}  # process_name -> check if running

    def require(self, process_name: str, start_cmd: str,
                stop_cmd: Optional[str] = None,
                check_cmd: Optional[str] = None) -> 'ProgramRequirements':
        """
        Add a required process for this program.

        Args:
            process_name: Name of the process (e.g., 'redis', 'celery')
            start_cmd: Command to start the process
            stop_cmd: Command to stop the process (optional)
            check_cmd: Command to check if running (optional)

        Returns:
            Self for chaining
        """
        self.requires.append(process_name)
        self.start_commands[process_name] = start_cmd
        if stop_cmd:
            self.stop_commands[process_name] = stop_cmd
        if check_cmd:
            self.check_commands[process_name] = check_cmd
        return self


class ProcessManager:
    """
    Manages processes for all programs.

    Keeps track of what's running, what each program needs,
    and intelligently starts/stops services as programs are used.
    """

    def __init__(self):
        self.running_processes: Dict[str, ProcessInfo] = {}
        self.program_requirements: Dict[str, ProgramRequirements] = {}
        self.active_programs: Set[str] = set()  # Which programs are currently in use

        # Register known program requirements
        self._register_default_requirements()

    def _register_default_requirements(self):
        """Register requirements for the 4 current programs."""

        # Modeling requires Redis + Celery for background tasks
        modeling = ProgramRequirements('Modeling')
        modeling.require(
            'redis',
            start_cmd='redis-server --daemonize yes --port 6379',
            stop_cmd='redis-cli shutdown',
            check_cmd='redis-cli ping'
        ).require(
            'celery',
            start_cmd='celery -A tasks.celery worker --loglevel=info --detach',
            stop_cmd='pkill -f "celery.*worker"',
            check_cmd='pgrep -f "celery.*worker"'
        )
        self.program_requirements['Modeling'] = modeling

        # PeopleFinder - currently no special requirements, but could add:
        # - Redis for caching
        # - Celery for async searches
        # - ML model servers
        people_finder = ProgramRequirements('PeopleFinder')
        self.program_requirements['PeopleFinder'] = people_finder

        # ParametricCAD - no special requirements yet
        parametric = ProgramRequirements('ParametricCAD')
        self.program_requirements['ParametricCAD'] = parametric

        # DigitalFootprint - no special requirements yet
        footprint = ProgramRequirements('DigitalFootprint')
        self.program_requirements['DigitalFootprint'] = footprint

    def register_program(self, requirements: ProgramRequirements):
        """Register a new program's requirements."""
        self.program_requirements[requirements.name] = requirements

    def program_accessed(self, program_name: str) -> Dict[str, str]:
        """
        Called when a program is accessed/opened.
        Starts any required processes that aren't running.

        Args:
            program_name: Name of the program being accessed

        Returns:
            Dict of process_name -> status message
        """
        if program_name not in self.program_requirements:
            return {'error': f'Unknown program: {program_name}'}

        self.active_programs.add(program_name)
        requirements = self.program_requirements[program_name]
        results = {}

        for process_name in requirements.requires:
            if self._is_process_running(process_name):
                results[process_name] = 'already_running'
            else:
                # Start the process
                success = self._start_process(process_name, requirements)
                results[process_name] = 'started' if success else 'failed'

        return results

    def program_closed(self, program_name: str) -> Dict[str, str]:
        """
        Called when a program is closed.
        Stops processes if no other programs need them.

        Args:
            program_name: Name of the program being closed

        Returns:
            Dict of process_name -> status message
        """
        if program_name in self.active_programs:
            self.active_programs.remove(program_name)

        if program_name not in self.program_requirements:
            return {}

        requirements = self.program_requirements[program_name]
        results = {}

        for process_name in requirements.requires:
            # Check if any other active program needs this process
            still_needed = any(
                process_name in self.program_requirements[prog].requires
                for prog in self.active_programs
            )

            if not still_needed:
                # No one needs it, shut it down
                success = self._stop_process(process_name, requirements)
                results[process_name] = 'stopped' if success else 'failed'
            else:
                results[process_name] = 'kept_running'  # Other programs still need it

        return results

    def _is_process_running(self, process_name: str) -> bool:
        """Check if a process is currently running."""
        # First check our tracked processes
        if process_name in self.running_processes:
            if self.running_processes[process_name].is_running():
                return True
            else:
                # Process died, remove from tracking
                del self.running_processes[process_name]

        # Check if process is running system-wide (might have been started externally)
        try:
            # Try to find the process
            for proc in psutil.process_iter(['name', 'cmdline']):
                try:
                    cmdline = ' '.join(proc.cmdline())
                    if process_name in cmdline.lower():
                        # Found it running
                        self.running_processes[process_name] = ProcessInfo(
                            process_name, proc.pid, cmdline
                        )
                        return True
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    continue
        except:
            pass

        return False

    def _start_process(self, process_name: str, requirements: ProgramRequirements) -> bool:
        """Start a process."""
        if process_name not in requirements.start_commands:
            return False

        cmd = requirements.start_commands[process_name]

        try:
            # Start the process
            result = subprocess.run(
                cmd,
                shell=True,
                capture_output=True,
                text=True,
                timeout=10
            )

            # Give it a moment to start
            time.sleep(1)

            # Check if it's running
            if self._is_process_running(process_name):
                print(f"✅ Started {process_name}")
                return True
            else:
                print(f"❌ Failed to start {process_name}")
                if result.stderr:
                    print(f"   Error: {result.stderr}")
                return False

        except subprocess.TimeoutExpired:
            print(f"⏱️  {process_name} start command timed out")
            return False
        except Exception as e:
            print(f"❌ Error starting {process_name}: {e}")
            return False

    def _stop_process(self, process_name: str, requirements: ProgramRequirements) -> bool:
        """Stop a process."""
        if process_name not in self.running_processes:
            return True  # Already stopped

        process_info = self.running_processes[process_name]

        # Try custom stop command first
        if process_name in requirements.stop_commands:
            try:
                subprocess.run(
                    requirements.stop_commands[process_name],
                    shell=True,
                    timeout=5
                )
                time.sleep(0.5)
            except:
                pass

        # Then try graceful stop
        success = process_info.stop()

        if success:
            del self.running_processes[process_name]
            print(f"🛑 Stopped {process_name}")

        return success

    def get_status(self) -> Dict:
        """Get current status of all processes and programs."""
        return {
            'active_programs': list(self.active_programs),
            'running_processes': {
                name: {
                    'pid': info.pid,
                    'running': info.is_running(),
                    'uptime': time.time() - info.started_at
                }
                for name, info in self.running_processes.items()
            },
            'registered_programs': {
                name: {
                    'requires': req.requires,
                    'optional': req.optional
                }
                for name, req in self.program_requirements.items()
            }
        }

    def cleanup_all(self):
        """Stop all managed processes (called on shutdown)."""
        print("\n🧹 Cleaning up all processes...")
        for process_name, process_info in list(self.running_processes.items()):
            # Find the requirements that started this process
            requirements = None
            for req in self.program_requirements.values():
                if process_name in req.requires:
                    requirements = req
                    break

            if requirements:
                self._stop_process(process_name, requirements)


# Global process manager instance
process_manager = ProcessManager()


if __name__ == '__main__':
    import json

    print("=" * 60)
    print("ZOOLZ PROCESS MANAGER")
    print("=" * 60)

    status = process_manager.get_status()
    print("\n📊 Current Status:")
    print(json.dumps(status, indent=2))

    print("\n💡 Example Usage:")
    print("  # User opens Modeling")
    print("  >>> process_manager.program_accessed('Modeling')")
    print("  # Starts Redis + Celery")
    print()
    print("  # User closes Modeling")
    print("  >>> process_manager.program_closed('Modeling')")
    print("  # Stops Redis + Celery (if no one else needs them)")
