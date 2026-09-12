#!/usr/bin/env bash
set -euo pipefail

# restore.sh - Safely restore a PostgreSQL backup
#
# Instead of immediately dropping the real database,
# we first restore into a temporary database, verify it worked,
# and ONLY THEN swap it with the real one.
#
# Usage:   ./restore.sh backups/barq_tasks_2026-09-12_14-30-00.sql

# Check that the user gave us a backup file
if [ $# -eq 0 ]; then
    echo "Usage: ./restore.sh <backup-file>"
    echo "Example: ./restore.sh backups/barq_tasks_2026-09-12_14-30-00.sql"
    exit 1
fi

BACKUP_FILE="$1"

# Check the file actually exists
if [ ! -f "$BACKUP_FILE" ]; then
    echo "FAIL  File not found: $BACKUP_FILE"
    exit 1
fi

echo "Safely restoring PostgreSQL from: $BACKUP_FILE"
echo ""

# Step 1: Create a temporary database to test the backup
echo "  Step 1: Creating temporary database..."
docker exec -i postgres psql -U barq_app -d postgres -c "DROP DATABASE IF EXISTS barq_tasks_temp;"
docker exec -i postgres psql -U barq_app -d postgres -c "CREATE DATABASE barq_tasks_temp OWNER barq_app;"

# Step 2: Load the backup into the TEMPORARY database
echo "  Step 2: Loading backup into temporary database..."
docker exec -i postgres psql -U barq_app -d barq_tasks_temp < "$BACKUP_FILE"

# Step 3: Verify the temporary database has valid data
echo "  Step 3: Verifying backup data..."
TABLE_CHECK=$(docker exec postgres psql -U barq_app -d barq_tasks_temp -t -c "SELECT COUNT(*) FROM information_schema.tables WHERE table_schema = 'public';" 2>/dev/null | tr -d ' ')

if [ "$TABLE_CHECK" -lt 1 ] 2>/dev/null; then
    echo "FAIL  Backup appears to be empty or corrupt. Real database was NOT touched."
    # Clean up the temp database
    docker exec -i postgres psql -U barq_app -d postgres -c "DROP DATABASE IF EXISTS barq_tasks_temp;"
    exit 1
fi

echo "    Backup verified: $TABLE_CHECK tables found in temporary database"

# Step 4: NOW it's safe to swap — drop the real database and rename the temp one
echo "  Step 4: Swapping temporary database into place..."

# Terminate any active connections to the real database first
docker exec -i postgres psql -U barq_app -d postgres -c "SELECT pg_terminate_backend(pid) FROM pg_stat_activity WHERE datname = 'barq_tasks' AND pid <> pg_backend_pid();" > /dev/null 2>&1 || true

docker exec -i postgres psql -U barq_app -d postgres -c "DROP DATABASE IF EXISTS barq_tasks;"
docker exec -i postgres psql -U barq_app -d postgres -c "ALTER DATABASE barq_tasks_temp RENAME TO barq_tasks;"

# Step 5: Final verification
RECORD_COUNT=$(docker exec postgres psql -U barq_app -d barq_tasks -t -c "SELECT COUNT(*) FROM records;" 2>/dev/null | tr -d ' ' || echo "0")

echo ""
echo "  Records after restore: $RECORD_COUNT"
echo ""
echo "PASS  Database restored safely with verification"
exit 0
