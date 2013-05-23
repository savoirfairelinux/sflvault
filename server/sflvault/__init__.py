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

import xmlrpclib
import functools
import logging

import sys

log = logging.getLogger(__name__)

def main(file_name):

    # We import in the main() function to avoid messing with namespace mechanism. We have to avoid
    # any code/import other than the declare_namespace() in a namespace pkg's init. See
    # http://packages.python.org/distribute/setuptools.html#namespace-packages

    # Monkeypatches the xmlrpclib to set partial application of allow_none
    #
    # sflvault relies on a behaviour provided by an older version of pylons_xmlrpc
    # that set the allow_none parameter by default. However, pyramid uses 
    # the new pyramid_rpc module that doesn't set this parameter and does not provide
    # any way of setting it manually.
    #
    xmlrpclib.dumps = functools.partial(xmlrpclib.dumps, allow_none=True)

    #from pyramid.config import Configurator
    from sqlalchemy import engine_from_config
    #from controller.xmlrpc import SflVaultController

    from sflvault import model
    from sflvault.model import init_model
    from sflvault.lib.vault import SFLvaultAccess

    from datetime import datetime, timedelta
    import transaction
    print "settings: %s" % settings

    # Configure the Pyramid app and SQL engine

    config = Configurator(settings=settings)
    config.include('pyramid_rpc.xmlrpc')
    config.add_xmlrpc_endpoint('sflvault', '/vault/rpc')
    config.scan('sflvault.views')

    # Configures the vault
    if 'sflvault.vault.session_timeout' in settings:
        SFLvaultAccess.session_timeout = settings['sflvault.vault.session_timeout']

    if 'sflvault.vault.setup_timeout' in settings:
        SFLvaultAccess.setup_timeout = settings['sflvault.vault.setup_timeout']

    # Configure sqlalchemy
    engine = engine_from_config(settings, 'sqlalchemy.')
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

if __name__ == '__main__':
    import ipdb; ipdb.set_trace()
    print sys.args
    if sys.argv:
        config_file = sys.argv[0]
