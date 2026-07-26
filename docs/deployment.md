# Cargo Marketplace — Deployment Guide

## Prerequisites

| Requirement | Version | Notes |
|-------------|---------|-------|
| Ubuntu | 22.04 LTS or 24.04 LTS | Recommended OS |
| Python | 3.10+ | System Python |
| PostgreSQL | 15+ | |
| Odoo | 18.0 Community | |
| RAM | 4 GB minimum | 8 GB recommended for production |
| Disk | 20 GB minimum | For data, logs, and filestore |

---

## Option 1: Docker (Development / Staging)

```bash
# Clone the repository
git clone https://github.com/Mohamedkajo/odoo_cargo.git
cd odoo_cargo

# Copy and configure environment
cp .env.example .env
# Edit .env with your passwords

# Start services
docker compose up -d

# Check logs
docker compose logs -f odoo

# Access Odoo at http://localhost:8069
# Create database and install Cargo modules via the web UI
```

**First-time database setup** (via Docker):
```bash
docker compose exec odoo odoo \
    --init=cargo_base,cargo_api \
    --database=cargo_db \
    --without-demo=all \
    --stop-after-init
```

---

## Option 2: Bare-Metal Ubuntu (Production)

```bash
# Clone the repository
git clone https://github.com/Mohamedkajo/odoo_cargo.git
cd odoo_cargo

# Run the installer (as root)
sudo bash install.sh
```

The installer handles everything: PostgreSQL, Python venv, Odoo 18, systemd service, and database initialisation.

### Post-Install Steps

1. **Configure Nginx** (reverse proxy):
   ```nginx
   server {
       listen 80;
       server_name api.yourdomain.com;
       location / {
           proxy_pass http://127.0.0.1:8069;
           proxy_set_header Host $host;
           proxy_set_header X-Real-IP $remote_addr;
           proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
           proxy_set_header X-Forwarded-Proto $scheme;
       }
       location /longpolling {
           proxy_pass http://127.0.0.1:8072;
       }
   }
   ```

2. **SSL with Let's Encrypt**:
   ```bash
   apt install certbot python3-certbot-nginx
   certbot --nginx -d api.yourdomain.com
   ```

3. **Configure Cargo settings** in Odoo:
   - Settings → Cargo → General Configuration
   - Verify JWT secret was generated (do NOT set it manually)
   - Set support email, phone, commission rate

---

## Updating Cargo Modules

After pulling new module code:

```bash
cd odoo_cargo
git pull

# Update specific modules
./scripts/update_modules.sh cargo_base,cargo_api

# Or update all
./scripts/update_modules.sh
```

---

## Running Tests

```bash
# All cargo tests
./tests/run_tests.sh

# Specific module
./tests/run_tests.sh cargo_base
./tests/run_tests.sh cargo_api

# With Docker
docker compose exec odoo odoo \
    --test-enable \
    --test-tags=/cargo_base,/cargo_api \
    --init=cargo_base,cargo_api \
    --stop-after-init
```

---

## Backup and Restore

```bash
# Backup
./scripts/backup.sh                  # creates timestamped dump in ./backups/

# Restore
pg_restore -U cargo_user -d cargo_db backups/cargo_db_20260726_030000.dump
```

---

## Flutter App Configuration

Update `lib/core/config/api_config.dart` in the Flutter Customer App:

```dart
class ApiConfig {
  // Development
  static const String devBaseUrl = 'http://localhost:8069/api/v1';
  
  // Staging
  static const String stagingBaseUrl = 'https://staging.api.yourdomain.com/api/v1';
  
  // Production
  static const String prodBaseUrl = 'https://api.yourdomain.com/api/v1';
  
  // Active
  static const String baseUrl = prodBaseUrl;
}
```

The existing Flutter Customer App requires **zero UI changes** — only the base URL changes.

---

## Environment Variables

See `.env.example` for all available configuration options.

Critical settings for production:
- `POSTGRES_PASSWORD` — strong random password
- `ODOO_ADMIN_PASSWD` — Odoo master password (protects database manager)
- `ENVIRONMENT=production`

---

## Monitoring

```bash
# Odoo service status
systemctl status odoo

# Odoo logs
journalctl -u odoo -f
tail -f /var/log/odoo/odoo.log

# PostgreSQL connections
psql -U cargo_user -d cargo_db -c "SELECT count(*) FROM pg_stat_activity;"

# API health check
curl http://localhost:8069/api/v1/health
```
