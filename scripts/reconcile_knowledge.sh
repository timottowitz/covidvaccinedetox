#!/usr/bin/env bash
set -Eeuo pipefail

# Robust reconcile script
# Usage:
#   BACKEND_URL=https://your-backend.example.com /app/scripts/reconcile_knowledge.sh
#   /app/scripts/reconcile_knowledge.sh https://your-backend.example.com
# Or set BACKEND_URL in repo root .env (see .env.example)

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")"/.. && pwd)"
ENV_FILE="${ROOT_DIR}/.env"

# Source repo root .env if present (does not touch frontend env)
if [[ -f "$ENV_FILE" ]]; then
  # shellcheck disable=SC1090
  source "$ENV_FILE"
fi

# Accept override via env or CLI arg
BACKEND_URL="${BACKEND_URL:-${1:-}}"
if [[ -z "${BACKEND_URL:-}" ]]; then
  echo "ERROR: BACKEND_URL not set. Set it in ${ENV_FILE}, export it, or pass as the first argument." >&2
  exit 2
fi

URL="${BACKEND_URL%/}/api/knowledge/reconcile"

# Curl with retries; fail-fast; log-friendly output
curl -fsS \
  --retry 3 --retry-connrefused --retry-delay 2 \
  -X POST "$URL" \
  -H "Content-Type: application/json" \
  -d '{}' \
  | sed 's/^/[reconcile]/'

echo "[reconcile] done at $(date -Is)"