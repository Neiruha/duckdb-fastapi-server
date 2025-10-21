#!/usr/bin/env bash
set -euo pipefail

BASE="${BASE:-https://neiruha.space/api/v1}"
TOKEN="${TOKEN:-}"
AUTH_HEADER=()
if [[ -n "$TOKEN" ]]; then
  AUTH_HEADER=(-H "Authorization: Bearer $TOKEN")
fi

call() {
  local method="$1"
  local path="$2"
  local body="$3"
  echo "\n>>> ${method} ${BASE}${path}" >&2
  if [[ -n "$body" ]]; then
    curl -s -X "$method" "${AUTH_HEADER[@]}" -H "Content-Type: application/json" -d "$body" "${BASE}${path}" | jq
  else
    curl -s -X "$method" "${AUTH_HEADER[@]}" "${BASE}${path}" | jq
  fi
}

echo "Health:"
call GET "/health" ""

echo "Connect session (autocreate user+frozen):"
call POST "/sessions/connect" '{"telegram_user_id": 555777999, "telegram_username":"demo_user","session_type":"bot","user_agent":"tg","ip_hash":"demo"}'

echo "Flags by telegram:"
call GET "/flags/telegram/555777999" ""

echo "Big profile:"
call GET "/profiles/by-telegram/555777999" ""
