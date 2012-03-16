#!/bin/bash
#
# SFLvault - Secure networked password store and credentials manager.
#
# Copyright (C) 2008-2009  Savoir-faire Linux inc.
#
# Author: Alexandre Bourget <alexandre.bourget@savoirfairelinux.com>
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

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
coverage html -d ../htmlcov

exit $EXIT_CODE
