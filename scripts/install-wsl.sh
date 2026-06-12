#!/usr/bin/env bash
# KARAKURI WSL/Ubuntu side setup (ROS 2 path later)
# Run from repo root inside WSL: bash scripts/install-wsl.sh

set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$REPO_ROOT"

echo "KARAKURI WSL/Ubuntu installer"
echo "  Root: $REPO_ROOT"
echo ""

if ! command -v git >/dev/null 2>&1; then
  echo "Installing git..."
  sudo apt-get update
  sudo apt-get install -y git
fi

if ! command -v python3 >/dev/null 2>&1; then
  echo "Installing python3..."
  sudo apt-get update
  sudo apt-get install -y python3 python3-venv python3-pip
fi

if ! python3 -m venv --help >/dev/null 2>&1; then
  echo "Installing python3-venv..."
  sudo apt-get update
  sudo apt-get install -y python3-venv
fi

PY_VERSION="$(python3 -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")')"
PY_MAJOR="${PY_VERSION%%.*}"
PY_MINOR="${PY_VERSION#*.}"
if [ "$PY_MAJOR" -lt 3 ] || { [ "$PY_MAJOR" -eq 3 ] && [ "$PY_MINOR" -lt 10 ]; }; then
  echo "Error: Python 3.10+ required (found $PY_VERSION)." >&2
  exit 1
fi
echo "  Python: $PY_VERSION"

if [ ! -d .venv ] || [ ! -f .venv/bin/activate ]; then
  echo "Creating virtual environment..."
  rm -rf .venv
  python3 -m venv .venv
fi

# shellcheck disable=SC1091
source .venv/bin/activate

python -m pip install --upgrade pip setuptools wheel
pip install -e ".[dev]"

if [ ! -f .env ]; then
  cp .env.example .env
  echo "Created .env from .env.example"
fi

echo ""
echo "Running karakuri doctor..."
python -m karakuri doctor || DOCTOR_EXIT=$?
DOCTOR_EXIT="${DOCTOR_EXIT:-0}"

echo ""
echo "Next steps:"
echo "  source .venv/bin/activate"
echo "  karakuri doctor"
echo "  karakuri stop --clear && karakuri run --once"
echo ""
echo "ROS 2 (Phase 2+): install distro packages in this WSL instance, then build robot/ws."
echo "See docs/WINDOWS.md and docs/ROBOT-MISSION.md."

exit "$DOCTOR_EXIT"
