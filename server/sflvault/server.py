import ConfigParser
from datetime import datetime, timedelta
from SimpleXMLRPCServer import SimpleXMLRPCServer, SimpleXMLRPCRequestHandler, SimpleXMLRPCDispatcher
import SocketServer
from BaseHTTPServer import HTTPServer
import os
import sys
import logging
import logging.config
import argparse
import socket

import transaction
from sqlalchemy import engine_from_config
from OpenSSL import SSL

import sflvault.model
from sflvault.views import XMLRPCDispatcher

log = logging.getLogger(__name__)

# SSL handling based on http://code.activestate.com/recipes/496786-simple-xml-rpc-server-over-https/

class SFLvaultRequestHandler(SimpleXMLRPCRequestHandler):

    def __init__(self, request, client_address, server):
        self.client_address = client_address
        SimpleXMLRPCRequestHandler.__init__(self, request, client_address, server)

    def setup(self):
        self.connection = self.request
        self.rfile = socket._fileobject(self.request, "rb", self.rbufsize)
        self.wfile = socket._fileobject(self.request, "wb", self.wbufsize)

    def _dispatch(self, method, params):
        address = self.client_address

        request = {
            'REMOTE_ADDR': address[0],
            'PORT': address[1],
            'rpc_args': params,
            'settings': SFLvaultServer.settings,
        }

        return self.server.instance._dispatch(request, method, params)

    rpc_paths = ('/vault', '/vault/rpc', '/',)

class SecureXMLRPCServer(HTTPServer, SimpleXMLRPCDispatcher):
    def __init__(self, server_address, requestHandler, keyfile, certfile, logRequests=True, allow_none=False):
        """Secure XML-RPC server.

        It it very similar to SimpleXMLRPCServer but it uses HTTPS for transporting XML data.
        """
        self.logRequests = logRequests

        SimpleXMLRPCDispatcher.__init__(self, allow_none=allow_none)
        SocketServer.BaseServer.__init__(self, server_address, requestHandler)
        ctx = SSL.Context(SSL.SSLv23_METHOD)
        ctx.use_privatekey_file(keyfile)
        ctx.use_certificate_file(certfile)
        self.socket = SSL.Connection(ctx, socket.socket(self.address_family, self.socket_type))
        self.server_bind()
        self.server_activate()

    def shutdown_request(self, request):
        # Our SSL connection doesn't take an argument on shutdown so we have to override the method
        # that calls it.
        try:
            #explicitly shutdown.  socket.close() merely releases
            #the socket and waits for GC to perform the actual close.
            request.shutdown()
        except socket.error:
            pass #some platforms may raise ENOTCONN here
        self.close_request(request)

class SFLvaultServer(object):

    def __init__(self, config_file_name):
        self.server = None
        SFLvaultServer.settings = self.get_settings(config_file_name)

        self.start_sqlalchemy()
        self.initialize_models()
        self.create_admin_if_necessary()
        self.initialize_server()
        
    def get_settings(self, config_file_name=None):
        result = {
            'sflvault.vault.session_timeout': '15',
            'sflvault.vault.setup_timeout': '300',
            'sflvault.host': 'localhost',
            'sflvault.port': '5000',
            'sqlalchemy.url': 'sqlite:///%s/sflvault.db' % os.getcwd()
        }
        if config_file_name:
            config = ConfigParser.ConfigParser()
            config.read(config_file_name)
            result.update(self.get_dict_for_config_section(config, 'sflvault'))
        return result

    def start_sqlalchemy(self):
        self.engine = engine_from_config(SFLvaultServer.settings,
                                    'sqlalchemy.')

    def initialize_models(self):
        sflvault.model.init_model(self.engine)
        sflvault.model.meta.metadata.create_all(self.engine)

    def create_admin_if_necessary(self):
        if not sflvault.model.query(sflvault.model.User).filter_by(username='admin').first():
            log.info ("It seems like you are using SFLvault for the first time. An\
                'admin' user account will be added to the system.")
            u = sflvault.model.User()
            u.waiting_setup = datetime.now() + timedelta(0,900)
            u.username = u'admin'
            u.created_time = datetime.now()
            u.is_admin = True
            #transaction.begin()
            sflvault.model.meta.Session.add(u)
            transaction.commit()

    def initialize_server(self):
        dispatcher = self._create_request_dispatcher()
        host = SFLvaultServer.settings['sflvault.host']
        port = int(SFLvaultServer.settings['sflvault.port'])
        address = (host, port)
        keyfile = SFLvaultServer.settings.get('sflvault.keyfile')
        certfile = SFLvaultServer.settings.get('sflvault.certfile')
        if keyfile and certfile:
            log.info("Starting in SSL mode")
            self.server = SecureXMLRPCServer(
                address,
                requestHandler=SFLvaultRequestHandler,
                keyfile=keyfile,
                certfile=certfile,
                logRequests=False,
                allow_none=True,
            )
        else:
            log.info("Starting in insecure mode")
            self.server = SimpleXMLRPCServer(
                address,
                requestHandler=SFLvaultRequestHandler,
                logRequests=False,
                allow_none=True,
            )
        self.server.register_introspection_functions()
        self.server.register_instance(dispatcher)

    def _create_request_dispatcher(self):
        dispatcher = XMLRPCDispatcher()
        dispatcher.scan(sflvault.views)
        return dispatcher

    def start_server(self):
        self.server.serve_forever()

    def get_dict_for_config_section(self, config, section):
        my_dict = {} 
        for key in config._sections[section].keys():
            my_dict[key] = config.get(section, key, 0,
                                      {'here': os.getcwd()})
        return my_dict

def main():
    parser = argparse.ArgumentParser(description="Launch the SFLVault server")
    parser.add_argument('config_file', nargs='?', default=None,
        help="INI config file")
    args = parser.parse_args()
    if args.config_file:
        logging.config.fileConfig(args.config_file)
    server = SFLvaultServer(args.config_file)
    server.start_server()

if __name__ == '__main__':
    main()
