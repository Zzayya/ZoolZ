#!/bin/bash
# Auto-backup ModelingSaves every hour

BACKUP_DIR="$HOME/Desktop/ZoolZ_Backups"
SOURCE_DIR="$HOME/Desktop/ZoolZ/programs/Modeling/ModelingSaves"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)

mkdir -p "$BACKUP_DIR"

if [ -d "$SOURCE_DIR" ]; then
    echo "🔄 Backing up ModelingSaves..."
    rsync -av "$SOURCE_DIR/" "$BACKUP_DIR/backup_$TIMESTAMP/"
    
    # Keep only last 10 backups
    cd "$BACKUP_DIR"
    ls -t | tail -n +11 | xargs rm -rf 2>/dev/null
    
    echo "✅ Backup complete: backup_$TIMESTAMP"
else
    echo "⚠️  Source directory not found"
fi
