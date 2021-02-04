#!/usr/bin/env bash
#
# Commentary:
#
# This script combines a Guix environment created via the manifest.scm
# file with a Python virtualenv, used to install the SFLvault-common
# and SFLwault-client packages in 'editable' mode.  This is necessary
# because SFLvault-client uses pkg_resources to discover entry-points
# (which are created at installation time).
#
set -e

this_dir=$(dirname "$0")
has_guix=0
python_version=
venv=venv

cd "$this_dir"

if command -v guix > /dev/null; then
    has_guix=1
    venv=guix_venv
fi

activate_venv="\
if [ \"$has_guix\" = 1 ]; then
    # Share the system libraries so the custom python-keyring-1.6 Guix
    # package is available.
    test -d \"$venv\" || virtualenv --system-site-packages \"$venv\"
else
    test -d \"$venv\" || virtualenv \"$venv\"
fi

# Activate the virtualenv.
source \"$venv\"/bin/activate

# Install sflvault in 'editable' mode.
pip install --editable ./common ./client
"

# Create venv if it doesn't already exists.
if [ "$has_guix" = 1 ]; then
    venv=guix_venv
    guix time-machine -C channels.scm \
         -- environment --pure --preserve=SSL_CERT -m manifest.scm \
         -- bash --init-file <(echo ". \"$HOME/.bashrc\"; $activate_venv")
else
    python_version=$(python3 --version | cut -d' ' -f2)
    if ! python3 -c 'from base64 import decodestring' 2>/dev/null; then
        echo "error: Your Python version is too recent, please install Guix"
        exit 1
    fi
    venv=venv
    bash --init-file <(echo ". \"$HOME/.bashrc\"; $activate_venv")
fi

# You can then use sflvault the usual way while working on the code.
