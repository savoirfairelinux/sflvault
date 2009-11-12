# -=- encoding: utf-8 -=-
#
# SFLvault - Secure networked password store and credentials manager.
#
# Copyright (C) 2008  Savoir-faire Linux inc.
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

"""The base Controller API

Provides the BaseController class for subclassing, and other objects
utilized by Controllers.
"""
from pylons import c, cache, config, g, request, response, session
from pylons.controllers import WSGIController, XMLRPCController
from pylons.controllers.util import abort, etag_cache, redirect_to
from pylons.decorators import jsonify, validate
from pylons.i18n import _, ungettext, N_
from pylons.templating import render
from datetime import *
import xmlrpclib

import sflvault.lib.helpers as h
from sflvault import model
from sflvault.model import query
from sflvault.common.crypto import *
from sflvault.common import VaultError

from base64 import b64decode, b64encode


# Helper to return messages

def vaultMsg(success, message, dict=None):
    """Form return message understandable by vault client"""
    ret = {'error': (not success), 'message': message}
    if dict:
        for x in dict:
            ret[x] = dict[x]
    return ret


#
# Session management functions
#
def _setup_sessions():
    """DRY out set_session and get_session"""
    if not hasattr(g, 'vaultSessions'):
        g.vaultSessions = {}

def set_session(authtok, value):
    """Sets in 'g.vaultSessions':
    {authtok1: {'username':  , 'timeout': datetime}, authtok2: {}..}
    
    """
    _setup_sessions();

    g.vaultSessions[authtok] = value;
        
def get_session(authtok):
    """Return the values associated with a session"""
    _setup_sessions();

    if not g.vaultSessions.has_key(authtok):
        return None

    if not g.vaultSessions[authtok].has_key('timeout'):
        g.vaultSessions[authtok]['timeout'] = datetime.now() + timedelta(0, SESSION_TIMEOUT)
    
    if g.vaultSessions[authtok]['timeout'] < datetime.now():
        del(g.vaultSessions[authtok])
        return None

    if g.vaultSessions[authtok]['remote_addr'] != request.environ.get('REMOTE_ADDR', 'gibberish'):
        del(g.vaultSessions[authtok])
        return None

    return g.vaultSessions[authtok]



class BaseController(WSGIController):
    def __call__(self, environ, start_response):
        """Invoke the Controller"""
        # WSGIController.__call__ dispatches to the Controller method
        # the request is routed to. This routing information is
        # available in environ['pylons.routes_dict']
        try:
            return WSGIController.__call__(self, environ, start_response)
        finally:
            model.meta.Session.remove()

# XMLRPC definition bac in xmlrpc.py


# Include the '_' function in the public names
__all__ = [__name for __name in locals().keys() if not __name.startswith('_') \
           or __name == '_']
