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

__all__ = ['url_for', 'TestController']

here_dir = os.path.dirname(os.path.abspath(__file__))
conf_dir = os.path.dirname(os.path.dirname(here_dir))

sys.path.insert(0, conf_dir)
pkg_resources.working_set.add_entry(conf_dir)
pkg_resources.require('Paste')
pkg_resources.require('PasteScript')

# Remove the test database on each run.
dbfile = os.path.join(conf_dir, 'test-database.db')
if os.path.exists(dbfile):
    os.unlink(dbfile)

test_file = os.path.join(conf_dir, 'test.ini')
cmd = paste.script.appinstall.SetupCommand('setup-app')
cmd.run([test_file])


class TestController(TestCase):


    def setUp(self, *args, **kwargs):
        print "\t--------------------------------------------------------------"
        print "\t--- Setting up database test environment, please stand by. ---"
        print "\t--------------------------------------------------------------"

        self.globs = {}

        infos = ConfigParser()
        infos.read(test_file)
        sinfos = infos._sections['server:main']
        wsgiapp = loadapp('config:test.ini', relative_to=conf_dir)
        server = self.globs['server'] = serve(wsgiapp,
                                     sinfos['host'],
                                     sinfos['port'],
                                     socket_timeout=1,
                                     start_loop=False,
                                    )
        t = threading.Thread(target=server.serve_forever)
        t.setDaemon(True)
        t.start()
        #self.globs['app'] = paste.fixture.TestApp(wsgiapp)
        
        #def url_for_wrapper(*args, **kwargs):
        #    lkwargs = {'protocol': 'http' ,'host':  "%s:%s" % \
        #               (server.server_name, server.server_port)}
        #    lkwargs.update(kwargs)
        #    return url_for(*args, **lkwargs)
        #self.globs['url_for'] = url_for_wrapper
        #self.globs['url_for_orig'] = url_for

    def tearDown(self):
        self.globs['server'].server_close()



    def __init__(self, *args, **kwargs):
        wsgiapp = loadapp('config:test.ini', relative_to=conf_dir)
        self.app = paste.fixture.TestApp(wsgiapp)

        # Create the vault test obj.
        if 'SFLVAULT_ASKPASS' in os.environ:
            del(os.environ['SFLVAULT_ASKPASS'])
        os.environ['SFLVAULT_CONFIG'] = config['sflvault.testconfig']
        
        self.vault = SFLvaultClient(shell=True)
        self.passphrase = 'test'
        self.username = 'admin'
        
        TestCase.__init__(self, *args, **kwargs)
