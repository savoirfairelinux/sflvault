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
import time
from unittest import TestCase

import pkg_resources
import paste.fixture
import paste.script.appinstall
from paste.deploy import loadapp
from ConfigParser import ConfigParser
from paste.httpserver import serve
import threading

from pylons import config
from sflvault.client import SFLvaultClient
from sflvault.lib.vault import SFLvaultAccess

__all__ = ['BaseTestCase', 'SFLvaultClient', 'vault']

here_dir = os.path.dirname(os.path.abspath(__file__))
conf_dir = os.path.dirname(os.path.dirname(here_dir))

sys.path.insert(0, conf_dir)
pkg_resources.working_set.add_entry(conf_dir)
pkg_resources.require('Paste')
pkg_resources.require('PasteScript')

vault = None


def tearDown():
    """Close the SFLVault server"""
    if os.path.exists('test-server.pid'):
        os.system("kill $(cat test-server.pid) ; rm test-server.pid")

def setUp():
    """Setup the temporary SFLvault server"""

    print "Wiping test directory"
    os.chdir(here_dir)
    os.system("rm test-server.ini")  # Remove server config
    os.system("rm sflvault.sqlite")  # Remove database
    os.system("rm test-config")  # Remove user config
    os.system("rm -f host.key host.pem host.cert")

    print "Creating test config, certificate, etc.."
    os.system("paster make-config SFLvault-server test-server.ini")
    os.system('sed -i "s/port = 5000/port = 5767/" test-server.ini')
    os.system("paster setup-app test-server.ini")
    os.system("openssl genrsa 1024 > host.key ; chmod 400 host.key ; openssl req -new -x509 -config test-certif-config -nodes -sha1 -days 365 -key host.key > host.cert ; cat host.cert host.key > host.pem ; chmod 400 host.pem")

    print "Launching server..."
    os.system("paster serve --pid-file test-server.pid test-server.ini &")

    # Create the vault test obj.
    if 'SFLVAULT_ASKPASS' in os.environ:
        del(os.environ['SFLVAULT_ASKPASS'])
    os.environ['SFLVAULT_CONFIG'] = os.path.join(here_dir, 'test-config')

    # Wait until the server is started
    time.sleep(1)


class BaseTestCase(TestCase):
    url = 'https://localhost:5767/vault/rpc'

    def __init__(self, *args, **kwargs):
        TestCase.__init__(self, *args, **kwargs)

    def getVault(self):
        """Get the SFLVault server vault"""
        global vault
        if vault is None:
            vault = SFLvaultClient(os.environ['SFLVAULT_CONFIG'],
                                                  shell=True)
            vault.passphrase = 'test'
            vault.username = 'admin'    

            def givepass():
                return vault.passphrase        
            vault.set_getpassfunc(givepass)
            vault.user_setup(vault.username, 
                             self.url, 
                             vault.passphrase)
            self.cfg = vault.cfg
        return vault
    
