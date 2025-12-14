"""
Program Launcher Logic

Handles booting up and managing programs within Zoolz.
Currently programs run as Flask blueprints in a single process.

Future expansion:
- Launch programs in separate processes/terminals
- Manage inter-process communication
- Monitor program health and restart if needed
- Load balancing for the 65+ programs coming
"""

import subprocess
import os
from typing import Dict, Optional, List
from pathlib import Path


class ProgramLauncher:
    """
    Manages launching and coordinating programs within Zoolz.

    Currently: Programs are Flask blueprints (no separate processes needed)
    Future: Could launch programs as separate processes for isolation/scaling
    """

    def __init__(self):
        self.running_programs: Dict[str, dict] = {}

    def register_program(self, name: str, blueprint_name: str, url_prefix: str):
        """
        Register a program with the launcher.

        Args:
            name: Program name (e.g., "Modeling")
            blueprint_name: Flask blueprint variable name
            url_prefix: URL prefix (e.g., "/modeling")
        """
        self.running_programs[name] = {
            'type': 'blueprint',
            'blueprint': blueprint_name,
            'url_prefix': url_prefix,
            'status': 'registered'
        }

    def get_registered_programs(self) -> List[str]:
        """Get list of all registered program names."""
        return list(self.running_programs.keys())

    def get_program_info(self, name: str) -> Optional[dict]:
        """Get information about a specific program."""
        return self.running_programs.get(name)

    # Future expansion methods for separate process management:

    def launch_separate_process(self, program_name: str, program_path: Path):
        """
        Launch a program in a separate process (future use).

        This would be used when programs become too complex to run as blueprints
        and need their own isolated processes.
        """
        # TODO: Implement when needed for the 65+ programs
        pass

    def stop_program(self, program_name: str):
        """Stop a running program (future use)."""
        # TODO: Implement when needed
        pass

    def restart_program(self, program_name: str):
        """Restart a program (future use)."""
        # TODO: Implement when needed
        pass

    def monitor_health(self):
        """Monitor health of all running programs (future use)."""
        # TODO: Implement when needed
        pass


# Global launcher instance
launcher = ProgramLauncher()


if __name__ == '__main__':
    print("ZoolZ Program Launcher")
    print("=" * 50)
    print("\nCurrently registered programs:")
    for name in launcher.get_registered_programs():
        info = launcher.get_program_info(name)
        print(f"  • {name}: {info['url_prefix']}")
