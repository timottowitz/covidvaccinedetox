#!/usr/bin/env bash
set -euo pipefail

# This script triggers backend knowledge reconciliation by calling
# the existing API endpoint using the configured backend URL.
# It is cron-friendly and prints a timestamped one-line log.

DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT="$(cd "$DIR/.." && pwd)"
ENV_FILE="$ROOT/frontend/.env"

# Read REACT_APP_BACKEND_URL from frontend/.env without modifying it
BACKEND_URL=""
if [[ -f "$ENV_FILE" ]]; then
  # shellcheck disable=SC2002
  RAW_URL=$(cat "$ENV_FILE" | grep -E '^REACT_APP_BACKEND_URL=' || true)
  if [[ -n "$RAW_URL" ]]; then
    BACKEND_URL=$(echo "$RAW_URL" | sed -E "s/^REACT_APP_BACKEND_URL=//; s/^\"?([^\"]+)\"?$/\1/")
  fi
fi

if [[ -z "${BACKEND_URL:-}" ]]; then
  echo "[$(date -u +"%Y-%m-%dT%H:%M:%SZ")] ERROR: REACT_APP_BACKEND_URL not found in $ENV_FILE" >&2
  exit 1
fi

URL="${BACKEND_URL%/}/api/knowledge/reconcile"
TS=$(date -u +"%Y-%m-%dT%H:%M:%SZ")

# Call the endpoint with short timeouts
RESP=$(curl -sS -X POST --connect-timeout 5 --max-time 20 -H "Content-Type: application/json" "$URL" 2>&1 || true)
CODE=$?

if [[ $CODE -ne 0 ]]; then
  echo "[$TS] ERROR calling $URL code=$CODE resp=$RESP"
  exit $CODE
fi

echo "[$TS] reconcile POST -> $URL; resp=$RESP"
