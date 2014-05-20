# -=- encoding: utf-8 -=-
#
# SFLvault - Secure networked password store and credentials manager.
#
# Copyright (C) 2014 Savoir-faire Linux inc.
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

"""Pylons application test package

When the test runner finds and executes tests within this directory,
this file will be loaded to setup the test environment.

It registers the root directory of the project in sys.path and
pkg_resources, in case the project hasn't been installed with
setuptools. It also initializes the application via websetup (paster
setup-app) with the project's test.ini configuration file.
"""
import os
import sys
from unittest import TestCase

import pkg_resources

from sflvault.client import SFLvaultClient

__all__ = ['BaseTestCase', 'SFLvaultClient', 'vault']

here_dir = os.path.dirname(os.path.abspath(__file__))
conf_dir = os.path.dirname(os.path.dirname(here_dir))

sys.path.insert(0, conf_dir)
pkg_resources.working_set.add_entry(conf_dir)

vault = None

def setUp():
    """Setup the temporary SFLvault server"""

    # Create the vault test obj.
    if 'SFLVAULT_ASKPASS' in os.environ:
        del(os.environ['SFLVAULT_ASKPASS'])
    os.environ['SFLVAULT_CONFIG'] = os.path.join(here_dir, 'sandbox/test-config')


class BaseTestCase(TestCase):
    url = 'https://localhost:5767/vault/rpc'

    def getVault(self):
        """Get the SFLVault server vault"""
        global vault
        if vault is None:
            vault = SFLvaultClient(os.environ['SFLVAULT_CONFIG'], shell=True)
            vault.passphrase = u'test'
            vault.username = u'admin'    

            def givepass():
                return vault.passphrase        
            vault.set_getpassfunc(givepass)
            vault.user_setup(vault.username, 
                             self.url, 
                             vault.passphrase)
            self.cfg = vault.cfg
        return vault
