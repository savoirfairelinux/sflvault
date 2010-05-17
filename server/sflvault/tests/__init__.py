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
import paste.fixture
import paste.script.appinstall
from paste.deploy import loadapp
from routes import url_for
from ConfigParser import ConfigParser
from paste.httpserver import serve
import threading

from pylons import config
from sflvault.client import SFLvaultClient
from sflvault.lib.vault import SFLvaultAccess

__all__ = ['url_for', 'TestController', 'setUp', 'tearDown']

here_dir = os.path.dirname(os.path.abspath(__file__))
conf_dir = os.path.dirname(os.path.dirname(here_dir))

sys.path.insert(0, conf_dir)
pkg_resources.working_set.add_entry(conf_dir)
pkg_resources.require('Paste')
pkg_resources.require('PasteScript')

dbfile = os.path.join(conf_dir, 'test-database.db')
confile = os.path.join(conf_dir, 'test-config')
test_file = os.path.join(conf_dir, 'test.ini')
globs = {}
vault = None


def tearDown():
    """Close the SFLVault server"""
    globs['server'].server_close()


def setUp():
    """Setup the temporary SFLvault server"""
    # Remove the test database on each run.
    if os.path.exists(dbfile):
        os.unlink(dbfile)

    # Remove the test config on each run
    if os.path.exists(confile):
        os.unlink(confile)

    cmd = paste.script.appinstall.SetupCommand('setup-app')
    cmd.run([test_file])

    cfg = ConfigParser()
    cfg.read(test_file)
    sinfos = cfg._sections['server:main']
    wsgiapp = loadapp('config:test.ini', relative_to=conf_dir)
    server = serve(wsgiapp, sinfos['host'], sinfos['port'],
                   socket_timeout=1, start_loop=False)
    globs['server'] = server
    t = threading.Thread(target=server.serve_forever)
    t.setDaemon(True)
    t.start()

    wsgiapp = loadapp('config:test.ini', relative_to=conf_dir)
    app = paste.fixture.TestApp(wsgiapp)

    # Create the vault test obj.
    if 'SFLVAULT_ASKPASS' in os.environ:
        del(os.environ['SFLVAULT_ASKPASS'])
    os.environ['SFLVAULT_CONFIG'] = config['sflvault.testconfig']        



class TestController(TestCase):
    def __init__(self, *args, **kwargs):
        TestCase.__init__(self, *args, **kwargs)

    def getVault(self):
        """Get the SFLVault server vault"""
        import sflvault.tests
        if sflvault.tests.vault is None:
            sflvault.tests.vault = SFLvaultClient(os.environ['SFLVAULT_CONFIG'],
                                                  shell=True)
            sflvault.tests.vault.passphrase = 'test'
            sflvault.tests.vault.username = 'admin'    

            def givepass():
                return sflvault.tests.vault.passphrase        
            sflvault.tests.vault.set_getpassfunc(givepass)
            sflvault.tests.vault.user_setup(sflvault.tests.vault.username, 
                                            'http://localhost:5551/vault/rpc', 
                                            sflvault.tests.vault.passphrase)
            self.cfg = sflvault.tests.vault.cfg
        return sflvault.tests.vault
    
