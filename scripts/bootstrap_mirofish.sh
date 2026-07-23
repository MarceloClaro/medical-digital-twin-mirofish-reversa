#!/usr/bin/env bash
set -euo pipefail
DEST="${1:-vendor/MiroFish}"
if [[ -e "$DEST" ]]; then
  echo "Destino já existe: $DEST" >&2
  exit 1
fi
mkdir -p "$(dirname "$DEST")"
git clone --depth 1 https://github.com/666ghj/MiroFish.git "$DEST"
printf '\nMiroFish foi clonado separadamente em %s. Leia LICENSE (AGPL-3.0) e .env.example antes de executar.\n' "$DEST"
