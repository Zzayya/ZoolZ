"""
Folder Manager - Server Data Structure Setup

Handles creation and management of the ZoolZData folder structure on the server.
When Zoolz runs on the server for the first time, it "moves in and sets up shop"
by creating organized folders for all data, keeping the code directory clean.
"""

import os
import shutil
from pathlib import Path
from typing import Dict, Optional
from .detection import is_server


# Server data root - ALL server data lives here (NOT synced)
# Uses HOME directory - works for any Mac username
SERVER_DATA_ROOT = Path.home() / "Desktop" / "ZoolZData"

# Laptop data root - uses local folders within the project
LAPTOP_DATA_ROOT = Path(__file__).parent.parent  # Points to ZoolZ project root


def get_data_root() -> Path:
    """
    Get the appropriate data root based on environment.

    Returns:
        Path: Server data root if on server, laptop project root if on laptop
    """
    return SERVER_DATA_ROOT if is_server() else LAPTOP_DATA_ROOT


def get_data_paths() -> Dict[str, Path]:
    """
    Get all data folder paths for the current environment.

    Returns:
        Dict[str, Path]: Dictionary of folder names to paths

    Example:
        >>> paths = get_data_paths()
        >>> print(paths['database'])
        /Users/isaiahmiro/Desktop/ZoolZData/database  (on server)
        /Users/isaiahmiro/Desktop/ZoolZ/database      (on laptop)
    """
    root = get_data_root()

    # If on laptop, use existing relative paths
    if not is_server():
        return {
            'root': root,
            'database': root / 'database',
            'uploads': root / 'programs' / 'Modeling' / 'ModelingSaves' / 'uploads',
            'outputs': root / 'programs' / 'Modeling' / 'outputs',
            'modeling_saves': root / 'programs' / 'Modeling' / 'ModelingSaves',
            'logs': root / 'logs',
            'program_data': root / 'program-data',
        }

    # Server uses MOSTLY ZoolZData, BUT keeps ModelingSaves in ZoolZ for syncing
    # ModelingSaves stays in synced ZoolZ folder so customer orders sync between laptop/server
    code_root = Path(__file__).parent.parent  # ZoolZ folder
    return {
        'root': root,
        'database': root / 'database',
        'uploads': root / 'uploads',
        'outputs': root / 'outputs',
        'modeling_saves': code_root / 'programs' / 'Modeling' / 'ModelingSaves',  # STAYS IN ZOOLZ
        'logs': root / 'logs',
        'program_data': root / 'program-data',
        'temp': root / 'temp',
        'cache': root / 'cache',
    }


def setup_server_folders(verbose: bool = True) -> Dict[str, bool]:
    """
    Create the ZoolZData folder structure on the server.

    This is called on first run on the server to "move in and set up shop".
    Creates all necessary folders for data storage outside the synced code directory.

    Args:
        verbose: If True, print creation messages

    Returns:
        Dict[str, bool]: Status of each folder creation (True if created, False if already existed)

    Example:
        >>> if is_server():
        ...     setup_server_folders()
        Creating ZoolZData folder structure...
        ✓ Created: /Users/isaiahmiro/Desktop/ZoolZData/database
        ✓ Created: /Users/isaiahmiro/Desktop/ZoolZData/uploads
        ...
    """
    if not is_server():
        if verbose:
            print("⚠️  Not on server - skipping ZoolZData folder creation")
        return {}

    paths = get_data_paths()
    status = {}

    if verbose:
        print(f"\n🏗️  Setting up ZoolZData folder structure at: {paths['root']}\n")

    for name, path in paths.items():
        if name == 'root':
            continue

        existed = path.exists()

        if not existed:
            path.mkdir(parents=True, exist_ok=True)
            if verbose:
                print(f"  ✓ Created: {path}")
            status[name] = True
        else:
            if verbose:
                print(f"  - Already exists: {path}")
            status[name] = False

    if verbose:
        print(f"\n✅ Server folders ready!\n")

    return status


def migrate_existing_data(dry_run: bool = True, verbose: bool = True) -> Dict[str, str]:
    """
    Migrate existing data from the code directory to ZoolZData.

    This is useful when first setting up the server - it moves existing data
    (databases, uploads, saved models) from the synced code directory to the
    new ZoolZData structure.

    Args:
        dry_run: If True, only show what would be moved (don't actually move)
        verbose: If True, print migration messages

    Returns:
        Dict[str, str]: Status messages for each migration operation

    Example:
        >>> # First do a dry run to see what would happen
        >>> migrate_existing_data(dry_run=True)
        >>> # Then actually do the migration
        >>> migrate_existing_data(dry_run=False)
    """
    if not is_server():
        return {'error': 'Not on server - migration only runs on server'}

    code_root = LAPTOP_DATA_ROOT  # The synced code directory
    data_root = SERVER_DATA_ROOT

    migrations = []
    results = {}

    # Database files
    old_db = code_root / 'database'
    new_db = data_root / 'database'
    if old_db.exists() and not dry_run:
        migrations.append(('database', old_db, new_db))

    # Modeling saves (customer orders, etc.)
    old_saves = code_root / 'programs' / 'Modeling' / 'ModelingSaves'
    new_saves = data_root / 'ModelingSaves'
    if old_saves.exists():
        migrations.append(('modeling_saves', old_saves, new_saves))

    # Uploads
    old_uploads = code_root / 'programs' / 'Modeling' / 'ModelingSaves' / 'uploads'
    new_uploads = data_root / 'uploads'
    if old_uploads.exists():
        migrations.append(('uploads', old_uploads, new_uploads))

    # Outputs
    old_outputs = code_root / 'programs' / 'Modeling' / 'outputs'
    new_outputs = data_root / 'outputs'
    if old_outputs.exists():
        migrations.append(('outputs', old_outputs, new_outputs))

    if verbose:
        mode = "DRY RUN - " if dry_run else ""
        print(f"\n📦 {mode}Migrating existing data to ZoolZData...\n")

    for name, old_path, new_path in migrations:
        if not old_path.exists():
            results[name] = f"Source not found: {old_path}"
            continue

        if dry_run:
            # Count files
            file_count = sum(1 for _ in old_path.rglob('*') if _.is_file()) if old_path.is_dir() else 1
            results[name] = f"Would move {file_count} files: {old_path} → {new_path}"
            if verbose:
                print(f"  • {name}: {file_count} files")
        else:
            try:
                # Create parent directory
                new_path.parent.mkdir(parents=True, exist_ok=True)

                # Move the data
                if old_path.is_dir():
                    shutil.copytree(old_path, new_path, dirs_exist_ok=True)
                    file_count = sum(1 for _ in new_path.rglob('*') if _.is_file())
                    results[name] = f"Copied {file_count} files to {new_path}"
                else:
                    shutil.copy2(old_path, new_path)
                    results[name] = f"Copied to {new_path}"

                if verbose:
                    print(f"  ✓ {name}: {results[name]}")
            except Exception as e:
                results[name] = f"Error: {str(e)}"
                if verbose:
                    print(f"  ✗ {name}: {str(e)}")

    if verbose:
        if dry_run:
            print(f"\n💡 This was a dry run. Run with dry_run=False to actually migrate.\n")
        else:
            print(f"\n✅ Migration complete!\n")

    return results


def ensure_folders_exist() -> None:
    """
    Ensure all required folders exist for the current environment.

    This is called at Zoolz startup to make sure everything is ready.
    On server: Creates ZoolZData structure if needed.
    On laptop: Creates any missing local folders.
    """
    paths = get_data_paths()

    for name, path in paths.items():
        if name == 'root':
            continue
        path.mkdir(parents=True, exist_ok=True)


def get_status() -> Dict[str, any]:
    """
    Get current folder manager status and diagnostics.

    Returns:
        Dict: Status information about the current environment and folders
    """
    paths = get_data_paths()

    status = {
        'environment': 'server' if is_server() else 'laptop',
        'data_root': str(get_data_root()),
        'folders': {}
    }

    for name, path in paths.items():
        if name == 'root':
            continue

        exists = path.exists()
        file_count = sum(1 for _ in path.rglob('*') if _.is_file()) if exists and path.is_dir() else 0

        status['folders'][name] = {
            'path': str(path),
            'exists': exists,
            'file_count': file_count if exists else 0
        }

    return status


if __name__ == '__main__':
    # Diagnostic output when run directly
    import json
    from .detection import verify_server_setup

    print("=" * 60)
    print("ZOOLZ FOLDER MANAGER DIAGNOSTICS")
    print("=" * 60)

    # Server detection
    server_info = verify_server_setup()
    print("\n📍 Environment Detection:")
    print(f"  Environment: {server_info['environment']}")
    print(f"  Server marker exists: {server_info['marker_exists']}")

    # Folder status
    print("\n📂 Folder Status:")
    status = get_status()
    print(f"  Data Root: {status['data_root']}")
    for name, info in status['folders'].items():
        icon = "✓" if info['exists'] else "✗"
        print(f"  {icon} {name}: {info['path']} ({info['file_count']} files)")

    print("\n" + "=" * 60)
