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


"""Pylons application test package

When the test runner finds and executes tests within this directory,
this file will be loaded to setup the test environment.

It registers the root directory of the project in sys.path and
pkg_resources, in case the project hasn't been installed with
setuptools. It also initializes the application via websetup (paster
setup-app) with the project's test.ini configuration file.
"""

# WARNING: For the moment, running the tests only works if you installed all sflvault packages
# (common, client, server) in "developer mode". If you don't, you'll have problems with namespace
# packaging and imports won't work.

import os
import sys
from unittest import TestCase


import threading

from sflvault.client import SFLvaultClient
from sflvault.lib.vault import SFLvaultAccess
from sflvault.server import SFLvaultServer
import logging
log = logging.getLogger(__name__)
__all__ = ['url_for', 'TestController', 'setUp', 'tearDown']

here_dir = os.path.dirname(os.path.abspath(__file__))
conf_dir = os.path.dirname(os.path.dirname(here_dir))

sys.path.insert(0, conf_dir)


dbfile = os.path.join(conf_dir, 'test-database.db')
confile = os.path.join(conf_dir, 'test-config')
userconfile = os.path.join(conf_dir, 'test-config-user')
test_file = os.path.join(conf_dir, 'test.ini')
globs = {}

def tearDown():
    """Close the SFLVault server"""
    #globs['server'].server_close()
    pass

def getConfFileAdmin():
    if (os.path.exists(confile)):
        os.unlink(confile)
    return confile 


def setUp():
    """Setup the temporary SFLvault server"""
    # Remove the test database on each run.
    if os.path.exists(dbfile):
        os.unlink(dbfile)
    # Remove the test config on each run
    if os.path.exists(confile):
        os.unlink(confile)

    os.environ['SFLVAULT_IN_TEST'] = 'true'

 
    server = SFLvaultServer(test_file)

    t = threading.Thread(target=server.start_server)
    t.setDaemon(True)
    t.start()

def delete_all_groups(self):

    vault_response = self.group_list()
    groups = vault_response['list']
    for group in groups:
        print "*** Deleting group: %s" % group['id']
        delete_cascade = True
        self.group_del(group['id'], delete_cascade=True)

def delete_all_users(self):

    vault_response = self.user_list()
    for user in vault_response['list']:
        if not (user['username'] == 'admin'):
            print "*** Deleting user: %s" % user['id']
            self.user_del(user['username'])

def delete_all_machines(self):
    vault_response = self.machine_list()
    for machine in vault_response['list']:
        print "*** Deleting machine: %s" % machine['id']
        self.machine_del(machine['id'])

def delete_all_customers(self):
    vault_response = self.customer_list()
    for customer in vault_response['list']:
        print "*** Deleting customer: %s" % customer['id']
        self.customer_del(customer['id'])


class TestController(TestCase):

    def __init__(self, *args, **kwargs):
        TestCase.__init__(self, *args, **kwargs)
        
    def getConfFileUser(self):
        if os.path.exists(userconfile):
            os.unlink(userconfile)
        return userconfile

    def tearDown(self):
        globs['vault'].delete_all_groups()
        globs['vault'].delete_all_users()
        globs['vault'].delete_all_machines()
        globs['vault'].delete_all_customers()

    def getVault(self):
        """Get the SFLVault server vault"""
        if 'vault' not in globs:
            SFLvaultClient.delete_all_groups = delete_all_groups
            SFLvaultClient.delete_all_users = delete_all_users
            SFLvaultClient.delete_all_machines = delete_all_machines
            SFLvaultClient.delete_all_customers = delete_all_customers

            vault =  SFLvaultClient(getConfFileAdmin(), shell=True)

            globs['vault'] = vault
            passphrase = u'test'
            username = u'admin'    

            def givepass():
                return passphrase        
            globs['vault'].set_getpassfunc(givepass)
            log.warn("testing user setup")
            globs['vault'].user_setup(username,
                'http://localhost:6555/vault/rpc', passphrase)
            globs['cfg'] = globs['vault'].cfg
        return globs['vault']

    
