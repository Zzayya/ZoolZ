"""
Server Health Monitor

Keeps an eye on Zoolz when running on the server.
Logs important events, monitors resource usage, and helps debug issues.
"""

import psutil
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, Optional
from .detection import is_server
from .folder_manager import get_data_paths


class HealthMonitor:
    """Monitors server health and logs events."""

    def __init__(self):
        self.start_time = time.time()
        self.log_file = None

        if is_server():
            # Create logs directory if on server
            paths = get_data_paths()
            log_dir = Path(paths['logs'])
            log_dir.mkdir(parents=True, exist_ok=True)

            # Create log file with timestamp
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            self.log_file = log_dir / f'zoolz_{timestamp}.log'

            self.log('SERVER', 'Zoolz started on server')
            self.log('HEALTH', f'Log file: {self.log_file}')

    def log(self, level: str, message: str):
        """Log a message with timestamp."""
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        log_message = f"[{timestamp}] [{level}] {message}"

        # Print to console
        print(log_message)

        # Write to file if on server
        if self.log_file:
            try:
                with open(self.log_file, 'a') as f:
                    f.write(log_message + '\n')
            except (OSError, IOError):
                pass  # Don't crash if logging fails

    def get_system_stats(self) -> Dict:
        """Get current system resource usage."""
        try:
            cpu_percent = psutil.cpu_percent(interval=1)
            memory = psutil.virtual_memory()
            disk = psutil.disk_usage('/')

            return {
                'cpu_percent': cpu_percent,
                'memory_percent': memory.percent,
                'memory_available_gb': memory.available / (1024**3),
                'disk_percent': disk.percent,
                'disk_free_gb': disk.free / (1024**3),
                'uptime_seconds': time.time() - self.start_time,
            }
        except (psutil.Error, OSError):
            return {}

    def log_system_stats(self):
        """Log current system stats."""
        stats = self.get_system_stats()
        if stats:
            self.log('STATS',
                    f"CPU: {stats['cpu_percent']:.1f}% | "
                    f"RAM: {stats['memory_percent']:.1f}% | "
                    f"Disk: {stats['disk_percent']:.1f}%")

    def check_health(self) -> Dict:
        """
        Check overall health and return status.

        Returns:
            Dict with health status and any warnings
        """
        stats = self.get_system_stats()
        warnings = []

        # Check for issues
        if stats.get('cpu_percent', 0) > 90:
            warnings.append('High CPU usage')

        if stats.get('memory_percent', 0) > 90:
            warnings.append('High memory usage')

        if stats.get('disk_percent', 0) > 90:
            warnings.append('Low disk space')

        if stats.get('memory_available_gb', 0) < 2:
            warnings.append('Low available memory (ML models need ~2GB)')

        status = 'healthy' if not warnings else 'warning'

        return {
            'status': status,
            'warnings': warnings,
            'stats': stats,
            'uptime_hours': stats.get('uptime_seconds', 0) / 3600
        }

    def log_program_access(self, program_name: str):
        """Log when a program is accessed."""
        self.log('ACCESS', f'User opened {program_name}')

    def log_process_start(self, process_name: str):
        """Log when a process is started."""
        self.log('PROCESS', f'Started {process_name}')

    def log_process_stop(self, process_name: str):
        """Log when a process is stopped."""
        self.log('PROCESS', f'Stopped {process_name}')

    def log_error(self, error_type: str, message: str):
        """Log an error."""
        self.log('ERROR', f'{error_type}: {message}')


# Global health monitor instance
health_monitor = HealthMonitor()


if __name__ == '__main__':
    import json

    print("=" * 60)
    print("ZOOLZ HEALTH MONITOR")
    print("=" * 60)
    print()

    # Check health
    health = health_monitor.check_health()

    print(f"Status: {health['status'].upper()}")
    print()

    if health['warnings']:
        print("⚠️  Warnings:")
        for warning in health['warnings']:
            print(f"  - {warning}")
        print()

    print("System Stats:")
    stats = health['stats']
    print(f"  CPU: {stats.get('cpu_percent', 0):.1f}%")
    print(f"  Memory: {stats.get('memory_percent', 0):.1f}% used")
    print(f"  Memory Available: {stats.get('memory_available_gb', 0):.1f} GB")
    print(f"  Disk: {stats.get('disk_percent', 0):.1f}% used")
    print(f"  Disk Free: {stats.get('disk_free_gb', 0):.1f} GB")
    print(f"  Uptime: {health.get('uptime_hours', 0):.2f} hours")
