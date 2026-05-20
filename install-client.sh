#!/usr/bin/env bash
# install-client.sh — Install the SFLvault client (Python 3) from the repository.
#
# Usage:
#   ./install-client.sh [--repo-dir /path/to/sflvault] [--venv /path/to/venv]
#
# Defaults:
#   --repo-dir  directory of this script  (i.e. the cloned repo)
#   --venv      ~/.sflvault-env
#
# The script will:
#   1. Create a Python 3 virtual environment
#   2. Install sflvault-common and sflvault-client from the repo
#   3. Symlink the `sflvault` binary to ~/.local/bin/sflvault
#
set -euo pipefail

# ---------- defaults ----------
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_DIR="$SCRIPT_DIR"
VENV_DIR="$HOME/.sflvault-env"

# ---------- parse args ----------
while [[ $# -gt 0 ]]; do
    case "$1" in
        --repo-dir) REPO_DIR="$2"; shift 2 ;;
        --venv)     VENV_DIR="$2"; shift 2 ;;
        -h|--help)
            sed -n '2,14p' "$0" | sed 's/^# \?//'
            exit 0
            ;;
        *) echo "Unknown option: $1" >&2; exit 1 ;;
    esac
done

COMMON_DIR="$REPO_DIR/common"
CLIENT_DIR="$REPO_DIR/client"

# ---------- git pull if inside a git repo ----------
if git -C "$REPO_DIR" rev-parse --is-inside-work-tree &>/dev/null; then
    echo "Updating repository..."
    git -C "$REPO_DIR" pull --ff-only || echo "WARNING: git pull failed, installing from current state"
fi

# ---------- sanity checks ----------
for dir in "$COMMON_DIR" "$CLIENT_DIR"; do
    if [[ ! -f "$dir/setup.py" ]]; then
        echo "ERROR: $dir/setup.py not found. Is --repo-dir pointing at the sflvault repo?" >&2
        exit 1
    fi
done

# ---------- require Python 3.9+ ----------
PYTHON=$(command -v python3 || true)
if [[ -z "$PYTHON" ]]; then
    echo "ERROR: python3 not found. Install python3 first." >&2
    exit 1
fi
PY_VER=$("$PYTHON" -c "import sys; print('%d.%d' % sys.version_info[:2])")
PY_MAJOR=$("$PYTHON" -c "import sys; print(sys.version_info[0])")
PY_MINOR=$("$PYTHON" -c "import sys; print(sys.version_info[1])")
if [[ "$PY_MAJOR" -lt 3 || ( "$PY_MAJOR" -eq 3 && "$PY_MINOR" -lt 9 ) ]]; then
    echo "ERROR: Python 3.9 or newer is required (found $PY_VER)." >&2
    exit 1
fi
echo "Using Python $PY_VER ($PYTHON)"

# ---------- create / reuse virtualenv ----------
if [[ ! -d "$VENV_DIR" ]]; then
    echo "Creating virtual environment at $VENV_DIR ..."
    "$PYTHON" -m venv "$VENV_DIR"
else
    echo "Reusing existing virtual environment at $VENV_DIR"
fi

PIP="$VENV_DIR/bin/pip"
"$PIP" install --quiet --upgrade pip

# ---------- install packages ----------
echo "Installing sflvault-common and sflvault-client ..."
"$PIP" install --quiet --force-reinstall "$COMMON_DIR" "$CLIENT_DIR"

# ---------- symlink binary ----------
SFLVAULT_BIN="$VENV_DIR/bin/sflvault"
LOCAL_BIN="$HOME/.local/bin"
mkdir -p "$LOCAL_BIN"

if [[ -L "$LOCAL_BIN/sflvault" || -f "$LOCAL_BIN/sflvault" ]]; then
    rm -f "$LOCAL_BIN/sflvault"
fi
ln -s "$SFLVAULT_BIN" "$LOCAL_BIN/sflvault"
echo "Symlinked $SFLVAULT_BIN → $LOCAL_BIN/sflvault"

# ---------- PATH reminder ----------
if ! echo "$PATH" | grep -q "$LOCAL_BIN"; then
    echo ""
    echo "NOTE: $LOCAL_BIN is not in your PATH."
    echo "Add this line to your ~/.bashrc or ~/.profile:"
    echo "  export PATH=\"\$HOME/.local/bin:\$PATH\""
fi

echo ""
echo "Installation complete. Run 'sflvault connect' to configure the client."
