#!/usr/bin/env bash
set -euo pipefail

# backup.sh - Back up the PostgreSQL database
#
# Usage:   ./backup.sh
# Output:  Creates a backup file in the backups/ folder
#          Filename includes the date and time so you never overwrite old backups

# Create the backups folder if it doesn't exist
mkdir -p backups

# Build the filename with the current date and time
TIMESTAMP=$(date +"%Y-%m-%d_%H-%M-%S")
BACKUP_FILE="backups/barq_tasks_${TIMESTAMP}.sql"

echo "Starting PostgreSQL backup..."

# Use pg_dump inside the postgres container to export the database
# -U barq_app  = connect as user barq_app
# barq_tasks   = the database name
docker exec postgres pg_dump -U barq_app barq_tasks > "$BACKUP_FILE"

# Check if the backup file was actually created and is not empty
if [ -s "$BACKUP_FILE" ]; then
    SIZE=$(wc -c < "$BACKUP_FILE")
    echo "PASS  Backup saved to: $BACKUP_FILE ($SIZE bytes)"
    exit 0
else
    echo "FAIL  Backup file is empty or was not created"
    exit 1
fi
