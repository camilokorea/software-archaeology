#!/usr/bin/env bash
# One command after cloning:
#   ./dig.sh /path/to/legacy-app [any archaeology dig option]
# Uses Docker when available (the analyzed repo is mounted read-only), otherwise a local Python environment.
set -euo pipefail

if [ $# -lt 1 ] || [ "${1:-}" = "-h" ] || [ "${1:-}" = "--help" ]; then
  echo "usage: ./dig.sh <path-to-repository> [--provider anthropic|ollama|none] [--depth quick|standard|deep] [...]"
  echo "       reports are written to ./archaeology-output/<repository name>/"
  exit 1
fi

HERE="$(cd "$(dirname "$0")" && pwd)"
REPO="$(cd "$1" && pwd)"; shift
NAME="$(basename "$REPO")"
OUT="$PWD/archaeology-output"
mkdir -p "$OUT"
CONFIG_ARGS=()
[ -f "$PWD/archaeology.yaml" ] && CONFIG_ARGS=(--config /config/archaeology.yaml)

if command -v docker >/dev/null 2>&1 && [ "${ARCHAEOLOGY_NO_DOCKER:-}" != "1" ]; then
  docker image inspect software-archaeology:2 >/dev/null 2>&1 || docker build -t software-archaeology:2 "$HERE"
  MOUNT_CONFIG=()
  [ -f "$PWD/archaeology.yaml" ] && MOUNT_CONFIG=(-v "$PWD/archaeology.yaml:/config/archaeology.yaml:ro")
  exec docker run --rm \
    -v "$REPO:/repo/$NAME:ro" -v "$OUT:/out" "${MOUNT_CONFIG[@]}" \
    -e ANTHROPIC_API_KEY -e OLLAMA_HOST \
    --user "$(id -u):$(id -g)" \
    software-archaeology:2 dig "/repo/$NAME" --out "/out/$NAME" "${CONFIG_ARGS[@]}" "$@"
fi

# Local fallback: a private virtual environment inside this clone.
VENV="$HERE/.venv"
if [ ! -x "$VENV/bin/archaeology" ]; then
  echo "Setting up a local environment in $VENV (once)…"
  python3 -m venv "$VENV"
  "$VENV/bin/pip" install --quiet -e "$HERE[anthropic]"
fi
[ -f "$PWD/archaeology.yaml" ] && CONFIG_ARGS=(--config "$PWD/archaeology.yaml")
exec "$VENV/bin/archaeology" dig "$REPO" --out "$OUT/$NAME" "${CONFIG_ARGS[@]}" "$@"
