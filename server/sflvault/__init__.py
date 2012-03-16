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
import logging
from pyramid.config import Configurator
from sqlalchemy import engine_from_config
#from controller.xmlrpc import SflVaultController
from sflvault.model import *
from datetime import datetime, timedelta
from pyramid_rpc.xmlrpc import xmlrpc_endpoint
import transaction
log = logging.getLogger(__name__)

def main(global_config, **settings):
    """ This function returns a Pyramid WSGI application.
    """
    print "Global config: %s " % global_config
    print "settings: %s" % settings
    engine = engine_from_config(settings, 'sqlalchemy.')
#    initialize_sql(engine)
    config = Configurator(settings=settings)
    config.add_route('RPC2', '/vault/rpc', view='pyramid_rpc.xmlrpc_endpoint')
    config.scan('sflvault.views')
#    config.add_view(SflVaultController,  route_name='xmlrpcvault')
#    session_factory = session_factory_from_settings(settings)
#    config.set_session_factory(session_factory)

    init_model(engine)
    model.meta.metadata.create_all(engine)
    #Add admin user if not present
    if not model.query(model.User).filter_by(username='admin').first():
        log.info ("It seems like you are using SFLvault for the first time. An\
                'admin' user account will be added to the system.")
        u = model.User()
        u.waiting_setup = datetime.now() + timedelta(0,900)
        u.username = u'admin'
        u.created_time = datetime.now()
        u.is_admin = True
        #transaction.begin()
        model.meta.Session.add(u)
        transaction.commit()
        log.info("Added 'admin' user, you have 15 minutes to setup from your client")
    return config.make_wsgi_app()

