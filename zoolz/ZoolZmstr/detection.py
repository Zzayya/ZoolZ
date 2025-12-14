"""
Server vs Laptop Detection Logic

Detects whether Zoolz is running on the Mac server or on the development laptop.
Uses a simple marker file check for reliable environment detection.
"""

import os
from pathlib import Path
from typing import Literal

# Marker file that only exists on the server
# YOU manually create this file on the server Desktop before running Zoolz
# Just: touch ~/Desktop/SERVER
# Uses HOME directory - works for any Mac username
SERVER_MARKER_FILE = Path.home() / "Desktop" / "SERVER"


def is_server() -> bool:
    """
    Check if Zoolz is running on the Mac server.

    Returns:
        bool: True if running on server, False if on laptop

    Example:
        >>> if is_server():
        ...     print("Running on Mac server - using ZoolZData folders")
        ... else:
        ...     print("Running on laptop - using local development folders")
    """
    return SERVER_MARKER_FILE.exists()


def get_environment() -> Literal['server', 'laptop']:
    """
    Get the current environment name.

    Returns:
        str: 'server' or 'laptop'

    Example:
        >>> env = get_environment()
        >>> print(f"Running in {env} environment")
    """
    return 'server' if is_server() else 'laptop'


def get_server_marker_path() -> Path:
    """
    Get the path where the server marker file should be located.

    Returns:
        Path: Path to the server marker file

    Note:
        To set up the server, manually create this file:
        touch /Users/isaiahmiro/Desktop/Zoolzmstr/.IM_THE_SERVER
    """
    return SERVER_MARKER_FILE


def verify_server_setup() -> dict:
    """
    Verify server setup and return diagnostic information.

    Returns:
        dict: Diagnostic information about the environment

    Example:
        >>> info = verify_server_setup()
        >>> print(f"Environment: {info['environment']}")
        >>> print(f"Server marker exists: {info['marker_exists']}")
        >>> print(f"Marker path: {info['marker_path']}")
    """
    marker_path = get_server_marker_path()
    marker_exists = marker_path.exists()

    return {
        'environment': get_environment(),
        'is_server': is_server(),
        'marker_exists': marker_exists,
        'marker_path': str(marker_path),
        'instructions': (
            "To set up server mode:\n"
            f"Create empty file on server Desktop: touch {marker_path}"
        ) if not marker_exists else "Server is configured ✓"
    }


if __name__ == '__main__':
    # Diagnostic output when run directly
    import json
    info = verify_server_setup()
    print(json.dumps(info, indent=2))
