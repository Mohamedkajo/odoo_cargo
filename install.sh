#!/usr/bin/env bash
# ─────────────────────────────────────────────────────────────────────────────
# Cargo Marketplace — One-shot installer for Ubuntu 22.04 / 24.04
#
# Usage:
#   chmod +x install.sh
#   sudo ./install.sh
#
# What it does:
#   1. Installs system dependencies (Python 3.10+, PostgreSQL 15, wkhtmltopdf)
#   2. Creates the odoo system user and PostgreSQL user
#   3. Clones Odoo 18 Community from GitHub
#   4. Installs Python requirements
#   5. Links the cargo addons into the Odoo addons path
#   6. Creates and enables the systemd service
#   7. Initialises the database with Cargo modules
# ─────────────────────────────────────────────────────────────────────────────

set -euo pipefail

# ── Configuration (override with environment variables) ───────────────────────
ODOO_VERSION="${ODOO_VERSION:-18.0}"
ODOO_HOME="${ODOO_HOME:-/opt/odoo}"
ODOO_USER="${ODOO_USER:-odoo}"
ODOO_PORT="${ODOO_PORT:-8069}"
DB_NAME="${DB_NAME:-cargo_db}"
DB_USER="${DB_USER:-cargo_user}"
DB_PASSWORD="${DB_PASSWORD:-$(openssl rand -hex 16)}"
CARGO_REPO="${CARGO_REPO:-$(pwd)}"
LOG_FILE="/var/log/cargo_install.log"

# ── Colours ───────────────────────────────────────────────────────────────────
RED='\033[0;31m'; GREEN='\033[0;32m'; YELLOW='\033[1;33m'; NC='\033[0m'

info()    { echo -e "${GREEN}[INFO]${NC}  $*" | tee -a "$LOG_FILE"; }
warn()    { echo -e "${YELLOW}[WARN]${NC}  $*" | tee -a "$LOG_FILE"; }
error()   { echo -e "${RED}[ERROR]${NC} $*" | tee -a "$LOG_FILE"; exit 1; }

# ── Pre-flight checks ─────────────────────────────────────────────────────────
[[ $EUID -ne 0 ]] && error "Run this script as root (sudo ./install.sh)"
[[ ! -f "$CARGO_REPO/addons/cargo_base/__manifest__.py" ]] && \
    error "Run install.sh from the odoo_cargo repository root."

touch "$LOG_FILE" && chmod 644 "$LOG_FILE"
info "=== Cargo Marketplace Installer — Odoo $ODOO_VERSION ==="
info "Log file: $LOG_FILE"

# ── Step 1: System dependencies ───────────────────────────────────────────────
info "Installing system dependencies..."
apt-get update -qq
apt-get install -y -qq \
    git curl wget gnupg2 lsb-release apt-transport-https ca-certificates \
    python3 python3-pip python3-venv python3-dev \
    build-essential libldap2-dev libsasl2-dev libssl-dev \
    libpq-dev libjpeg-dev libxml2-dev libxslt1-dev \
    node-less nodejs npm \
    postgresql-15 postgresql-client-15 \
    wkhtmltopdf \
    nginx \
    2>&1 | tee -a "$LOG_FILE"

# ── Step 2: PostgreSQL setup ──────────────────────────────────────────────────
info "Setting up PostgreSQL..."
systemctl start postgresql || true
systemctl enable postgresql

sudo -u postgres psql -c "CREATE USER $DB_USER WITH CREATEDB PASSWORD '$DB_PASSWORD';" \
    2>/dev/null || warn "PostgreSQL user $DB_USER already exists."
sudo -u postgres createdb -O "$DB_USER" "$DB_NAME" \
    2>/dev/null || warn "Database $DB_NAME already exists."

# ── Step 3: Odoo system user ──────────────────────────────────────────────────
info "Creating Odoo system user..."
id -u "$ODOO_USER" &>/dev/null || \
    useradd -m -d "$ODOO_HOME" -U -r -s /bin/bash "$ODOO_USER"

mkdir -p "$ODOO_HOME" /var/log/odoo /var/lib/odoo
chown -R "$ODOO_USER:$ODOO_USER" "$ODOO_HOME" /var/log/odoo /var/lib/odoo

# ── Step 4: Clone Odoo 18 ─────────────────────────────────────────────────────
ODOO_SRC="$ODOO_HOME/odoo"
if [[ ! -d "$ODOO_SRC/.git" ]]; then
    info "Cloning Odoo $ODOO_VERSION (this may take a few minutes)..."
    sudo -u "$ODOO_USER" git clone \
        --depth=1 --branch="$ODOO_VERSION" \
        https://github.com/odoo/odoo.git \
        "$ODOO_SRC" 2>&1 | tee -a "$LOG_FILE"
else
    info "Odoo source already exists at $ODOO_SRC — skipping clone."
fi

# ── Step 5: Python virtual environment ────────────────────────────────────────
VENV="$ODOO_HOME/venv"
info "Creating Python virtual environment at $VENV..."
sudo -u "$ODOO_USER" python3 -m venv "$VENV"
sudo -u "$ODOO_USER" "$VENV/bin/pip" install --upgrade pip wheel 2>&1 | tee -a "$LOG_FILE"
sudo -u "$ODOO_USER" "$VENV/bin/pip" install -r "$ODOO_SRC/requirements.txt" \
    2>&1 | tee -a "$LOG_FILE"
sudo -u "$ODOO_USER" "$VENV/bin/pip" install -r "$CARGO_REPO/requirements.txt" \
    2>&1 | tee -a "$LOG_FILE"

# ── Step 6: Link Cargo addons ─────────────────────────────────────────────────
CARGO_ADDONS="$ODOO_HOME/cargo_addons"
info "Linking Cargo addons to $CARGO_ADDONS..."
sudo -u "$ODOO_USER" ln -sfn "$CARGO_REPO/addons" "$CARGO_ADDONS"

# ── Step 7: Configuration file ────────────────────────────────────────────────
ODOO_CONF="/etc/odoo/odoo.conf"
info "Writing Odoo configuration to $ODOO_CONF..."
mkdir -p /etc/odoo
cat > "$ODOO_CONF" <<EOF
[options]
db_host     = localhost
db_port     = 5432
db_user     = $DB_USER
db_password = $DB_PASSWORD
db_name     = $DB_NAME
addons_path = $ODOO_SRC/addons,$CARGO_ADDONS
http_port   = $ODOO_PORT
workers     = 4
max_cron_threads = 2
logfile     = /var/log/odoo/odoo.log
log_level   = info
data_dir    = /var/lib/odoo
admin_passwd = $(openssl rand -hex 24)
EOF
chown "$ODOO_USER:$ODOO_USER" "$ODOO_CONF"
chmod 640 "$ODOO_CONF"

# ── Step 8: Systemd service ───────────────────────────────────────────────────
info "Installing systemd service..."
cat > /etc/systemd/system/odoo.service <<EOF
[Unit]
Description=Odoo 18 — Cargo Marketplace
After=network.target postgresql.service
Wants=postgresql.service

[Service]
Type=simple
User=$ODOO_USER
Group=$ODOO_USER
ExecStart=$VENV/bin/python $ODOO_SRC/odoo-bin --config=$ODOO_CONF
Restart=on-failure
RestartSec=5
StandardOutput=journal
StandardError=journal
SyslogIdentifier=odoo

[Install]
WantedBy=multi-user.target
EOF

systemctl daemon-reload
systemctl enable odoo

# ── Step 9: Initialise database with Cargo modules ────────────────────────────
info "Initialising database with cargo_base and cargo_api..."
sudo -u "$ODOO_USER" "$VENV/bin/python" "$ODOO_SRC/odoo-bin" \
    --config="$ODOO_CONF" \
    --init=cargo_base,cargo_api \
    --without-demo=all \
    --stop-after-init \
    2>&1 | tee -a "$LOG_FILE"

# ── Step 10: Start Odoo ───────────────────────────────────────────────────────
info "Starting Odoo service..."
systemctl start odoo
sleep 5
systemctl is-active odoo && info "Odoo is running!" || warn "Odoo may not have started — check: journalctl -u odoo -n 50"

# ── Done ──────────────────────────────────────────────────────────────────────
info ""
info "════════════════════════════════════════════════════════"
info " Installation complete!"
info ""
info " Odoo URL:   http://$(hostname -I | awk '{print $1}'):$ODOO_PORT"
info " Database:   $DB_NAME"
info " DB User:    $DB_USER"
info " DB Pass:    $DB_PASSWORD   ← save this!"
info " Log file:   /var/log/odoo/odoo.log"
info " Config:     $ODOO_CONF"
info ""
info " Next: Open the URL above and log in with admin / admin"
info " Then go to Settings → Cargo → Configure JWT and other settings"
info "════════════════════════════════════════════════════════"
