"""
Program Registry - Defines what services each program needs

This module knows which services (Redis, Celery, etc.) are required
for each program in ZoolZ.
"""

from typing import Dict, List, Set


class ProgramRegistry:
    """
    Registry of all programs and their service dependencies
    """

    # Define what services each program needs
    PROGRAM_DEPENDENCIES: Dict[str, List[str]] = {
        'modeling': ['redis', 'celery'],        # 3D Modeling needs background tasks
        'parametric': ['redis', 'celery'],      # Parametric CAD needs background tasks
        'people_finder': [],                    # People Finder is lightweight
        'digital_footprint': [],                # Digital Footprint is lightweight
    }

    # Program metadata
    PROGRAM_INFO: Dict[str, Dict] = {
        'modeling': {
            'name': '3D Modeling',
            'description': 'Cookie cutter generation and STL editing',
            'url_prefix': '/modeling',
            'heavy_processing': True,
        },
        'parametric': {
            'name': 'Parametric CAD',
            'description': 'OpenSCAD-like programmatic design',
            'url_prefix': '/parametric',
            'heavy_processing': True,
        },
        'people_finder': {
            'name': 'People Finder',
            'description': 'OSINT people research tool',
            'url_prefix': '/people_finder',
            'heavy_processing': False,
        },
        'digital_footprint': {
            'name': 'Digital Footprint',
            'description': 'Online presence analysis',
            'url_prefix': '/footprint',
            'heavy_processing': False,
        },
    }

    @classmethod
    def get_dependencies(cls, program_id: str) -> List[str]:
        """
        Get list of services required for a program

        Args:
            program_id: Program identifier (e.g., 'modeling')

        Returns:
            List of service names (e.g., ['redis', 'celery'])
        """
        return cls.PROGRAM_DEPENDENCIES.get(program_id, [])

    @classmethod
    def get_all_active_dependencies(cls, active_programs: List[str]) -> Set[str]:
        """
        Get unique set of all services needed for currently active programs

        Args:
            active_programs: List of currently running program IDs

        Returns:
            Set of unique service names needed
        """
        all_deps = set()
        for program_id in active_programs:
            deps = cls.get_dependencies(program_id)
            all_deps.update(deps)
        return all_deps

    @classmethod
    def get_program_info(cls, program_id: str) -> Dict:
        """Get metadata for a program"""
        return cls.PROGRAM_INFO.get(program_id, {})

    @classmethod
    def is_heavy_processing(cls, program_id: str) -> bool:
        """Check if program requires heavy processing"""
        info = cls.get_program_info(program_id)
        return info.get('heavy_processing', False)

    @classmethod
    def get_all_programs(cls) -> List[str]:
        """Get list of all registered programs"""
        return list(cls.PROGRAM_DEPENDENCIES.keys())
