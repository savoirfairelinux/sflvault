"""The base Controller API

Provides the BaseController class for subclassing, and other objects
utilized by Controllers.
"""
from pylons import c, cache, config, g, request, response, session
from pylons.controllers import WSGIController
from pylons.controllers.util import abort, etag_cache, redirect_to
from pylons.decorators import jsonify, validate
from pylons.i18n import _, ungettext, N_
from pylons.templating import render
from decorator import decorator
from datetime import *
import xmlrpclib

import sflvault.lib.helpers as h
import sflvault.model as model

from base64 import b64decode, b64encode
import pickle

# Helper to return messages

def vaultMsg(error, message, dict=None):
    """Form return message understandable by vault client"""
    ret = {'error': error, 'message': message}
    if dict:
        for x in dict:
            ret[x] = dict[x]
    return ret

#
# Serialization/unserialization
#
def vaultSerial(something):
    """Serialize with pickle.dumps + b64encode"""
    return b64encode(pickle.dumps(something))

def vaultUnserial(something):
    """Unserialize with b64decode + pickle.loads"""
    return pickle.loads(b64decode(something))



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

    return g.vaultSessions[authtok]

#
# Permissions decorators for XML-RPC calls
#

@decorator
def authenticated_user(func, self, *args, **kwargs):
    """Aborts if user isn't authenticated.

    Timeout check done in get_session.

    WARNING: authenticated_user READ the FIRST non-keyword argument
             (should be authtok)
    """
    s = get_session(args[0])

    if not s:
        return xmlrpclib.Fault(0, "Permission denied")

    self.sess = s

    return func(self, *args, **kwargs)

@decorator
def authenticated_admin(func, self, *args, **kwargs):
    """Aborts if user isn't admin.

    Check authenticated_user , everything written then applies here as well.
    """
    s = get_session(args[0])

    if not s:
        return xmlrpclib.Fault(0, "Permission denied")
    if not s['userobj'].is_admin:
        return xmlrpclib.Fault(0, "Permission denied, admin priv. required")

    self.sess = s

    return func(self, *args, **kwargs)



class BaseController(WSGIController):
    def __call__(self, environ, start_response):
        """Invoke the Controller"""
        # WSGIController.__call__ dispatches to the Controller method
        # the request is routed to. This routing information is
        # available in environ['pylons.routes_dict']
        try:
            return WSGIController.__call__(self, environ, start_response)
        finally:
            model.Session.remove()

# Include the '_' function in the public names
__all__ = [__name for __name in locals().keys() if not __name.startswith('_') \
           or __name == '_']
