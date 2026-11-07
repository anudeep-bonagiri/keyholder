#!/usr/bin/env bash
# One command a judge can run after cloning: fixture round-trip + template structure.
set -euo pipefail
cd "$(dirname "$0")/.."
echo "== fixture"
F=fixtures/checkout-service
$F/status.sh | grep -q DEGRADED && echo "ok  status reports DEGRADED on v2.14.0"
$F/rollback.sh --dry-run | grep -q "nothing changed" && echo "ok  dry run changes nothing"
$F/rollback.sh >/dev/null && $F/status.sh | grep -q HEALTHY && echo "ok  rollback restores HEALTHY on v2.13.3"
echo v2.14.0 > $F/releases/current; echo v2.13.3 > $F/releases/previous; git checkout -q $F/deploys.log 2>/dev/null || true
$F/status.sh | grep -q DEGRADED && echo "ok  fixture reset"
echo "== template"
python3 scripts/check_template.py keyholder.template.yaml
