#!/bin/bash

export COVERAGE_PROCESS_START=$PWD/.coveragerc

# run from the root of the workspace
rm -rf env
export PIP_DOWNLOAD_CACHE=$HOME/.pip/download_cache
./tests/preparetests.sh
. env/bin/activate
./tests/runtests.sh
EXIT_CODE=$?

# Compile coverage info
echo "Compiling coverage info..."
cd tests/sandbox
coverage combine
coverage xml

exit $EXIT_CODE
