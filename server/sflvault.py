# -=- encoding: utf-8 -=-
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

__import__('pkg_resources').declare_namespace(__name__)

import sys
import xmlrpclib
import logging.config
from sflvault.server import SFLvaultServer


if __name__ == '__main__':

    # FIXME: replace with argparse
    
    if len(sys.argv) == 2:
        config_file = sys.argv[1]
        logging.config.fileConfig(config_file)
        server = SFLvaultServer(config_file)
        server.start_server()

