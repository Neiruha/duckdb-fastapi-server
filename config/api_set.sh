# export_keys_min.sh
#!/usr/bin/env bash
cfg="${1:-./api_config.json}"
export OPEN_ROUTER_API_KEY="$(jq -r '.OPEN_ROUTER_API_KEY' "$cfg")"
export OPEN_AI_API_KEY="$(jq -r '.OPEN_AI_API_KEY' "$cfg")"
export GROQ_API_KEY="$(jq -r '.GROQ_API_KEY' "$cfg")"
