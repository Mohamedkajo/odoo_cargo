#!/usr/bin/env bash
# ─────────────────────────────────────────────────────────────────────────────
# backup.sh — Create a timestamped PostgreSQL backup
#
# Usage:
#   ./scripts/backup.sh                  # backup cargo_db to ./backups/
#   DB_NAME=cargo_staging ./scripts/backup.sh
# ─────────────────────────────────────────────────────────────────────────────

set -euo pipefail

DB_NAME="${DB_NAME:-cargo_db}"
DB_USER="${DB_USER:-cargo_user}"
BACKUP_DIR="${BACKUP_DIR:-$(pwd)/backups}"
TIMESTAMP="$(date +%Y%m%d_%H%M%S)"
BACKUP_FILE="$BACKUP_DIR/${DB_NAME}_${TIMESTAMP}.dump"

mkdir -p "$BACKUP_DIR"
echo "[INFO] Backing up $DB_NAME → $BACKUP_FILE"
pg_dump -U "$DB_USER" -Fc "$DB_NAME" > "$BACKUP_FILE"
echo "[INFO] Backup complete: $BACKUP_FILE ($(du -sh "$BACKUP_FILE" | cut -f1))"

# Keep only last 7 daily backups
find "$BACKUP_DIR" -name "${DB_NAME}_*.dump" -mtime +7 -delete 2>/dev/null || true
echo "[INFO] Old backups cleaned (keeping 7 days)."
