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


# Check if the reqs changed
# If the reqs match the previous, copy the previous environment
# Otherwise, create a new one, calc the hash and before going anywhere, copy it under here.
HASH=$(cat requirements.freeze|md5sum|cut -d' ' -f1)
if [ -e ../last_env_hash ]; then
  OLDHASH=$(cat ../last_env_hash)
else
  OLDHASH=""
fi
echo $HASH > ../last_env_hash

echo OLD REQS HASH AND NEW REQS HASH: $OLDHASH $HASH


# Cache the environment if it hasn't changed.
if [ "$OLDHASH" != "$HASH" ]; then
  echo "ENVIRONMENT SPECS CHANGED - CREATING A NEW ENVIRONMENT"
  virtualenv --distribute env
  #virtualenv env
  . env/bin/activate
  #pip install pip
  pip install -r requirements.freeze
  pip install -r requirements.tests.freeze

  rm -rf ../last_env
  cp -ar env ../last_env
else
  echo "ENVIRONMENT SPECS HAVE NOT CHANGED - USING CACHED ENVIRONMENT"
  cp -ar ../last_env env
  . env/bin/activate
fi;

#pip install -e common
#pip install -e client
#pip install -e server
#cd common && python setup.py develop && cd ..
#cd client && python setup.py develop && cd ..
cd server && python setup.py develop && cd ..
