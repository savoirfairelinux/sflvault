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
from pyramid import testing
import pkg_resources
import threading
import paste.fixture
from paste.deploy import loadapp
from paste.httpserver import serve
from sflvault.client import SFLvaultClient
from sflvault.lib.vault import SFLvaultAccess
import logging
log = logging.getLogger(__name__)
__all__ = ['url_for', 'TestController', 'setUp', 'tearDown']

here_dir = os.path.dirname(os.path.abspath(__file__))
conf_dir = os.path.dirname(os.path.dirname(here_dir))

sys.path.insert(0, conf_dir)
pkg_resources.working_set.add_entry(conf_dir)
pkg_resources.require('Paste')
pkg_resources.require('PasteScript')

dbfile = os.path.join(conf_dir, 'test-database.db')
confile = os.path.join(conf_dir, 'test-config')
userconfile = os.path.join(conf_dir, 'test-config-user')
test_file = os.path.join(conf_dir, 'test.ini')
globs = {}
vault = None



def tearDown():
    """Close the SFLVault server"""
    globs['server'].server_close()


def getConfFileAdmin():
    if (os.path.exists(confile)):
        os.unlink(confile)
    return confile 


def setUp():
    # Remove the test database on each run.
    if os.path.exists(dbfile):
        os.unlink(dbfile)
    # Remove the test config on each run
    if os.path.exists(confile):
        os.unlink(confile)
    """Setup the temporary SFLvault server"""
    wsgiapp = loadapp('config:test.ini', relative_to=conf_dir)
    app = paste.fixture.TestApp(wsgiapp)
    server = serve(wsgiapp, 'localhost', '6555',
                socket_timeout=1, start_loop=False)
    globs['server'] = server
    t = threading.Thread(target=server.serve_forever)
    t.setDaemon(True)
    t.start()

class TestController(TestCase):

    def __init__(self, *args, **kwargs):
        TestCase.__init__(self, *args, **kwargs)
        
    def getConfFileUser(self):
        if os.path.exists(userconfile):
            os.unlink(userconfile)
        return userconfile

        

    def getVault(self):
        if not globs.has_key('vault'):

            globs['vault'] = SFLvaultClient(getConfFileAdmin(), shell=True)
            passphrase = u'test'
            username = u'admin'    

            def givepass():
                return passphrase        
            globs['vault'].set_getpassfunc(givepass)
            log.warn("testing user setup")
            globs['vault'].user_setup(username, 
                                            'http://localhost:6555/vault/rpc', 
                                            passphrase)
            globs['cfg'] = globs['vault'].cfg
        """Get the SFLVault server vault"""
        return globs['vault']

    
