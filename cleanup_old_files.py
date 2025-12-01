#!/usr/bin/env python3
"""
Cleanup Script - Remove Old Duplicate Files After Reorganization

This script safely removes old duplicate files from the modeling program
reorganization. It will:
1. Show you what will be deleted
2. Ask for confirmation
3. Create a backup (optional)
4. Delete the files
5. Provide a summary

IMPORTANT: Only run this after verifying the new structure works!
"""

import os
import shutil
import sys
from datetime import datetime
from pathlib import Path

# Base directory
BASE_DIR = Path(__file__).parent.absolute()

# Files and directories to remove
OLD_FILES_TO_DELETE = [
    # Old modeling blueprint (duplicated in programs/modeling/)
    'blueprints/modeling.py',

    # Old modeling utilities (duplicated in programs/modeling/utils/)
    'utils/modeling/shape_generators.py',
    'utils/modeling/mesh_utils.py',
    'utils/modeling/scale.py',
    'utils/modeling/cut.py',
    'utils/modeling/channels.py',
    'utils/modeling/thicken.py',
    'utils/modeling/hollow.py',
    'utils/modeling/mirror.py',
    'utils/modeling/repair.py',
    'utils/modeling/simplify.py',
    'utils/modeling/__init__.py',
    'utils/modeling/',  # Directory itself

    # Old modeling JavaScript files (duplicated in programs/modeling/static/js/)
    'static/js/modeling_controller.js',
    'static/js/floating_windows.js',
    'static/js/selection_manager.js',
    'static/js/scene_manager.js',
    'static/js/transform_gizmo.js',
    'static/js/undo_redo.js',
    'static/js/advanced_tools.js',
    'static/js/new_tools.js',
    'static/js/shape_picker.js',
    'static/js/outline_editor.js',
    'static/js/outline_editor_v2.js',
    'static/js/ui_modernizer.js',
    'static/js/my_models.js',

    # Old modeling template (duplicated in programs/modeling/templates/)
    'templates/modeling.html',

    # Old modeling CSS (duplicated in programs/modeling/static/css/)
    'static/css/modeling_fixes.css',
]


def get_file_size(filepath):
    """Get human-readable file size"""
    try:
        size = os.path.getsize(filepath)
        for unit in ['B', 'KB', 'MB', 'GB']:
            if size < 1024.0:
                return f"{size:.1f} {unit}"
            size /= 1024.0
    except:
        return "N/A"


def check_files_exist():
    """Check which files actually exist"""
    existing = []
    missing = []
    total_size = 0

    for filepath in OLD_FILES_TO_DELETE:
        full_path = BASE_DIR / filepath
        if full_path.exists():
            existing.append(filepath)
            if full_path.is_file():
                total_size += os.path.getsize(full_path)
        else:
            missing.append(filepath)

    return existing, missing, total_size


def create_backup(files_to_backup):
    """Create a backup of files before deletion"""
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    backup_dir = BASE_DIR / f'backup_before_cleanup_{timestamp}'

    print(f"\n📦 Creating backup at: {backup_dir}")
    backup_dir.mkdir(parents=True, exist_ok=True)

    for filepath in files_to_backup:
        source = BASE_DIR / filepath
        dest = backup_dir / filepath

        if source.is_file():
            dest.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(source, dest)
            print(f"   ✓ Backed up: {filepath}")

    print(f"\n✅ Backup created successfully!")
    return backup_dir


def delete_files(files_to_delete):
    """Delete the specified files"""
    deleted_files = []
    deleted_dirs = []
    errors = []

    # Separate files and directories
    files = [f for f in files_to_delete if not f.endswith('/')]
    dirs = [f for f in files_to_delete if f.endswith('/')]

    # Delete files first
    for filepath in files:
        full_path = BASE_DIR / filepath
        try:
            if full_path.exists():
                os.remove(full_path)
                deleted_files.append(filepath)
                print(f"   ✓ Deleted: {filepath}")
        except Exception as e:
            errors.append(f"{filepath}: {e}")
            print(f"   ✗ Error deleting {filepath}: {e}")

    # Delete directories
    for dirpath in dirs:
        full_path = BASE_DIR / dirpath.rstrip('/')
        try:
            if full_path.exists() and full_path.is_dir():
                shutil.rmtree(full_path)
                deleted_dirs.append(dirpath)
                print(f"   ✓ Deleted directory: {dirpath}")
        except Exception as e:
            errors.append(f"{dirpath}: {e}")
            print(f"   ✗ Error deleting {dirpath}: {e}")

    return deleted_files, deleted_dirs, errors


def main():
    """Main cleanup function"""
    print("=" * 70)
    print("🧹 ZoolZ Cleanup Script - Remove Old Duplicate Files")
    print("=" * 70)

    # Check what exists
    print("\n🔍 Scanning for old files...")
    existing, missing, total_size = check_files_exist()

    if not existing:
        print("\n✅ No old files found - cleanup already complete!")
        return

    # Show what will be deleted
    print(f"\n📋 Found {len(existing)} files/directories to delete:")
    print(f"💾 Total size: {total_size / (1024*1024):.2f} MB\n")

    for filepath in existing:
        full_path = BASE_DIR / filepath
        if full_path.is_file():
            size = get_file_size(full_path)
            print(f"   • {filepath} ({size})")
        else:
            print(f"   • {filepath} (directory)")

    if missing:
        print(f"\n⚠️  Note: {len(missing)} files already deleted or never existed")

    # Verify new structure is in place
    print("\n🔍 Verifying new structure exists...")
    critical_new_files = [
        'programs/modeling/blueprint.py',
        'programs/modeling/utils/shape_generators.py',
        'shared/cookie_logic.py',
    ]

    all_exist = True
    for filepath in critical_new_files:
        full_path = BASE_DIR / filepath
        if full_path.exists():
            print(f"   ✓ {filepath}")
        else:
            print(f"   ✗ MISSING: {filepath}")
            all_exist = False

    if not all_exist:
        print("\n❌ ERROR: New structure is incomplete!")
        print("   Do NOT run cleanup until reorganization is complete.")
        sys.exit(1)

    # Confirmation
    print("\n" + "=" * 70)
    print("⚠️  WARNING: This will permanently delete old duplicate files!")
    print("=" * 70)

    # Ask about backup
    backup_choice = input("\n📦 Create backup before deletion? (y/n): ").strip().lower()
    backup_dir = None

    if backup_choice == 'y':
        backup_dir = create_backup(existing)

    # Final confirmation
    print("\n⚠️  FINAL CONFIRMATION")
    confirm = input(f"\nDelete {len(existing)} old files? Type 'DELETE' to confirm: ").strip()

    if confirm != 'DELETE':
        print("\n❌ Cleanup cancelled by user")
        return

    # Delete files
    print("\n🗑️  Deleting old files...")
    deleted_files, deleted_dirs, errors = delete_files(existing)

    # Summary
    print("\n" + "=" * 70)
    print("📊 CLEANUP SUMMARY")
    print("=" * 70)
    print(f"   Files deleted: {len(deleted_files)}")
    print(f"   Directories deleted: {len(deleted_dirs)}")
    print(f"   Errors: {len(errors)}")
    if backup_dir:
        print(f"   Backup location: {backup_dir}")
    print()

    if errors:
        print("❌ Errors occurred:")
        for error in errors:
            print(f"   • {error}")
    else:
        print("✅ Cleanup completed successfully!")
        print("\n📝 Next steps:")
        print("   1. Test the application: python3 app.py")
        print("   2. Run tests: python3 -m pytest tests/ -v")
        print("   3. If everything works, delete the backup folder")

    print("\n" + "=" * 70)


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n❌ Cleanup cancelled by user (Ctrl+C)")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
