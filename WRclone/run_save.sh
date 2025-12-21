#!/usr/bin/env bash
set -euo pipefail

# Lance `save.py` depuis le venv local (.venv) ou le python système
script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
venv_py=""

if [ -x "$script_dir/.venv/bin/python" ]; then
  venv_py="$script_dir/.venv/bin/python"
fi

if [ -z "$venv_py" ] && [ -x "$script_dir/.venv/Scripts/python.exe" ]; then
  venv_py="$script_dir/.venv/Scripts/python.exe"
fi

if [ -z "$venv_py" ] && command -v python3 >/dev/null 2>&1; then
  venv_py="$(command -v python3)"
fi

if [ -z "$venv_py" ] && command -v python >/dev/null 2>&1; then
  venv_py="$(command -v python)"
fi

if [ -z "$venv_py" ]; then
  echo "Python not found. Create a virtualenv .venv or ensure python is on PATH." >&2
  exit 1
fi

save_py="$script_dir/save.py"
if [ ! -f "$save_py" ]; then
  echo "save.py not found in $script_dir" >&2
  exit 1
fi

echo "Using Python: $venv_py"
exec "$venv_py" "$save_py" "$@"
