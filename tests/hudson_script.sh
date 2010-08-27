#!/bin/bash

# ran from the root of the workspace
rm -rf env
export PIP_DOWNLOAD_CACHE=$HOME/.pip/download_cache

./tests/preparetests.sh
nosetests tests
