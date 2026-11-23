#!/usr/bin/env bash
# Usage: bash scripts/setkey.sh OPENAI_API_KEY
# Reads a key silently and stores it in ~/.swebench-keys.env (outside the repo, mode 600).
set -euo pipefail
name="${1:?usage: setkey.sh VAR_NAME}"
f="$HOME/.swebench-keys.env"
touch "$f"; chmod 600 "$f"
printf 'Paste %s (nothing will show), then press Return: ' "$name"
IFS= read -rs key
echo
key="$(printf '%s' "$key" | tr -d '[:space:]')"
if [ -z "$key" ]; then echo "EMPTY - nothing saved"; exit 1; fi
tmp="$(mktemp)"
grep -v "^export ${name}=" "$f" > "$tmp" || true
printf "export %s='%s'\n" "$name" "$key" >> "$tmp"
mv "$tmp" "$f"; chmod 600 "$f"
echo "saved $name: length ${#key}, starts with ${key:0:3}"
