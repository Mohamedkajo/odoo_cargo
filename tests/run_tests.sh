#!/usr/bin/env bash
# ─────────────────────────────────────────────────────────────────────────────
# run_tests.sh — Run Cargo module test suites via Odoo's test runner
#
# Usage:
#   ./tests/run_tests.sh                      # run all cargo tests
#   ./tests/run_tests.sh cargo_base           # run specific module tests
#   ./tests/run_tests.sh cargo_base cargo_api # run multiple modules
#
# Requires:
#   - Odoo 18 installed with cargo modules available
#   - A test database (created fresh for each run)
#   - ODOO_BIN and ODOO_CONF set, or defaults used
# ─────────────────────────────────────────────────────────────────────────────

set -euo pipefail

ODOO_BIN="${ODOO_BIN:-/opt/odoo/venv/bin/odoo-bin}"
ODOO_CONF="${ODOO_CONF:-/etc/odoo/odoo.conf}"
TEST_DB="${TEST_DB:-cargo_test_$(date +%s)}"
MODULES="${*:-cargo_base cargo_api}"
MODULES_CSV="${MODULES// /,}"
LOG_FILE="/tmp/cargo_test_${TEST_DB}.log"

echo "╔══════════════════════════════════════════════════════╗"
echo "║        Cargo Marketplace — Test Runner              ║"
echo "╚══════════════════════════════════════════════════════╝"
echo ""
echo "  Modules:  $MODULES_CSV"
echo "  Test DB:  $TEST_DB"
echo "  Log:      $LOG_FILE"
echo ""

RESULT=0

# Run Odoo tests with a fresh test database
"$ODOO_BIN" \
    --config="$ODOO_CONF" \
    --database="$TEST_DB" \
    --init="$MODULES_CSV" \
    --test-enable \
    --test-tags="/$MODULES_CSV" \
    --log-level=test \
    --stop-after-init \
    2>&1 | tee "$LOG_FILE" || RESULT=$?

echo ""
# Parse results from log
PASS=$(grep -c "^[0-9]\+\.[0-9]\+ INFO.*ok$" "$LOG_FILE" 2>/dev/null || echo 0)
FAIL=$(grep -c "^[0-9]\+\.[0-9]\+ ERROR.*FAIL" "$LOG_FILE" 2>/dev/null || echo 0)
ERROR=$(grep -c "ERROR.*at line" "$LOG_FILE" 2>/dev/null || echo 0)

echo "══════════════════════════════════════════════"
echo "  Results:"
echo "    Passed:  $PASS"
echo "    Failed:  $FAIL"
echo "    Errors:  $ERROR"
echo "══════════════════════════════════════════════"

# Drop the test database
if psql -U "${DB_USER:-cargo_user}" -lqt 2>/dev/null | cut -d\| -f1 | grep -qw "$TEST_DB"; then
    echo "  Dropping test database $TEST_DB..."
    dropdb -U "${DB_USER:-cargo_user}" "$TEST_DB" 2>/dev/null || true
fi

if [[ $RESULT -eq 0 && "$FAIL" -eq 0 ]]; then
    echo ""
    echo "  ✓ All tests passed."
    exit 0
else
    echo ""
    echo "  ✗ Tests FAILED. See $LOG_FILE for details."
    exit 1
fi
