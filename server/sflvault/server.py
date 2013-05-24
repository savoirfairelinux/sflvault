import ConfigParser
from datetime import datetime, timedelta
from SimpleXMLRPCServer import SimpleXMLRPCServer, SimpleXMLRPCRequestHandler
import os
import sys
import logging

import transaction
from sqlalchemy import engine_from_config

import sflvault.model
from sflvault.views import XMLRPCDispatcher

log = logging.getLogger(__name__)

class SFLvaultRequestHandler(SimpleXMLRPCRequestHandler):

    def __init__(self, request, client_address, server):
        self.client_address = client_address
        SimpleXMLRPCRequestHandler.__init__(self, request, client_address, server)

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

class SFLvaultServer(object):

    def __init__(self, config_file_name):
        self.server = None
        SFLvaultServer.settings = self.get_settings(config_file_name)

        self.start_sqlalchemy()
        self.initialize_models()
        self.create_admin_if_necessary()
        self.initialize_server()
        
    def get_settings(self, config_file_name):
        config = ConfigParser.ConfigParser({
            'sflvault.vault.session_timeout': 15,
            'sflvault.vault.setup_timeout': 300,
            'sflvault.port': 5001,
        })
        config.read(config_file_name)
        return self.get_dict_for_config_section(config, 'sflvault')

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
        self.server = SimpleXMLRPCServer(("localhost",
                                          int(SFLvaultServer.settings['sflvault.port'])),
                                    requestHandler=SFLvaultRequestHandler,
                                    allow_none=True)
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
