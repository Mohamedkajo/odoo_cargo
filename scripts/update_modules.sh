#!/usr/bin/env bash
# ─────────────────────────────────────────────────────────────────────────────
# update_modules.sh — Update (upgrade) one or more Cargo modules
#
# Usage:
#   ./scripts/update_modules.sh                 # update all cargo modules
#   ./scripts/update_modules.sh cargo_base      # update specific module
#   ./scripts/update_modules.sh cargo_base,cargo_api
#
# Requires: Odoo to be installed and odoo-bin in PATH (or ODOO_BIN set)
# ─────────────────────────────────────────────────────────────────────────────

set -euo pipefail

ODOO_BIN="${ODOO_BIN:-/opt/odoo/venv/bin/odoo-bin}"
ODOO_CONF="${ODOO_CONF:-/etc/odoo/odoo.conf}"
DB_NAME="${DB_NAME:-cargo_db}"

# Default: update all Cargo modules
MODULES="${1:-cargo_base,cargo_api}"

echo "[INFO] Updating modules: $MODULES"
echo "[INFO] Database: $DB_NAME"
echo ""

# Stop Odoo service before update (prevents conflicts)
if systemctl is-active --quiet odoo 2>/dev/null; then
    echo "[INFO] Stopping Odoo service..."
    systemctl stop odoo
    RESTART_AFTER=true
else
    RESTART_AFTER=false
fi

# Run the update
"$ODOO_BIN" \
    --config="$ODOO_CONF" \
    --database="$DB_NAME" \
    --update="$MODULES" \
    --stop-after-init

echo ""
echo "[INFO] Module update complete."

# Restart if we stopped it
if [[ "$RESTART_AFTER" == "true" ]]; then
    echo "[INFO] Restarting Odoo service..."
    systemctl start odoo
fi

echo "[INFO] Done."
