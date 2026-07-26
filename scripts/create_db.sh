#!/usr/bin/env bash
# ─────────────────────────────────────────────────────────────────────────────
# create_db.sh — Create and initialise a fresh Cargo database
#
# Usage:
#   ./scripts/create_db.sh                      # creates cargo_db
#   DB_NAME=cargo_staging ./scripts/create_db.sh
#
# Options (environment variables):
#   DB_NAME     Database name            (default: cargo_db)
#   DB_USER     PostgreSQL user          (default: cargo_user)
#   ODOO_BIN    Path to odoo-bin         (default: /opt/odoo/venv/bin/odoo-bin)
#   ODOO_CONF   Path to odoo.conf        (default: /etc/odoo/odoo.conf)
#   MODULES     Comma-separated modules  (default: cargo_base,cargo_api)
# ─────────────────────────────────────────────────────────────────────────────

set -euo pipefail

DB_NAME="${DB_NAME:-cargo_db}"
DB_USER="${DB_USER:-cargo_user}"
ODOO_BIN="${ODOO_BIN:-/opt/odoo/venv/bin/odoo-bin}"
ODOO_CONF="${ODOO_CONF:-/etc/odoo/odoo.conf}"
MODULES="${MODULES:-cargo_base,cargo_api}"

echo "[INFO] Creating database: $DB_NAME"
echo "[INFO] Modules to install: $MODULES"
echo ""

# Create the PostgreSQL database
if psql -U "$DB_USER" -lqt 2>/dev/null | cut -d \| -f 1 | grep -qw "$DB_NAME"; then
    echo "[WARN] Database $DB_NAME already exists. Use --force to drop and recreate."
    read -p "Drop and recreate? [y/N] " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        echo "[INFO] Dropping database $DB_NAME..."
        dropdb -U "$DB_USER" "$DB_NAME"
    else
        echo "[INFO] Aborted."
        exit 0
    fi
fi

createdb -U "$DB_USER" "$DB_NAME"
echo "[INFO] Database created."

# Initialise with Odoo and Cargo modules
echo "[INFO] Installing modules (this may take several minutes)..."
"$ODOO_BIN" \
    --config="$ODOO_CONF" \
    --database="$DB_NAME" \
    --init="$MODULES" \
    --without-demo=all \
    --stop-after-init

echo ""
echo "[INFO] ═══════════════════════════════════════════════"
echo "[INFO] Database initialised: $DB_NAME"
echo "[INFO] Modules installed: $MODULES"
echo "[INFO] ═══════════════════════════════════════════════"
