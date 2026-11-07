#!/usr/bin/env bash
# Rolls checkout-service back to the previous release. This is the ONE
# state-changing action in the room. Run it with --dry-run to preview.
set -e
cd "$(dirname "$0")"
cur=$(cat releases/current); prev=$(cat releases/previous)
if [ "${1:-}" = "--dry-run" ]; then
  echo "DRY RUN: would roll checkout-service back from $cur to $prev"
  echo "DRY RUN: would append a rollback entry to deploys.log"
  echo "DRY RUN: nothing changed"
  exit 0
fi
echo "$prev" > releases/current
echo "$cur"  > releases/previous
echo "$(date -u +%Y-%m-%dT%H:%M:%SZ) rollback checkout-service $cur -> $prev by keyholder (approved in room)" >> deploys.log
echo "rolled checkout-service back from $cur to $prev"
./status.sh
