#!/usr/bin/env bash
# Prints the live state of checkout-service. Read-only.
cd "$(dirname "$0")"
cur=$(cat releases/current)
if [ "$cur" = "v2.14.0" ]; then
  echo "checkout-service  release=$cur  error_rate=18.7%  p95=2301ms  status=DEGRADED"
else
  echo "checkout-service  release=$cur  error_rate=0.3%  p95=414ms  status=HEALTHY"
fi
