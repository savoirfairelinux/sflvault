# -*- coding: utf-8 -*-
#
# SFLvault - Secure networked password store and credentials manager.
#
# Copyright (C) 2014 Savoir-faire Linux inc.
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

import logging
import transaction

from sflvault.common.crypto import *
from sflvault.lib.vault import SFLvaultAccess, vaultMsg
from sflvault.model import *
from decorator import decorator
from datetime import datetime, timedelta
from distutils.version import LooseVersion
import venusian

import sys

log = logging.getLogger(__name__)

MINIMAL_CLIENT_VERSION = LooseVersion('0.7.6')
# Permissions decorators for XML-RPC calls
#

vaultSessions = {}
vault = SFLvaultAccess()

def test_group_admin(request, group_id):
    if not query(Group).filter_by(id=group_id).first():
        return vaultMsg(False, "Group not found: %s" % str(group_id))
    
    sess = get_session(request['rpc_args'][0])

    # Verify if I'm is_admin on that group
    ug = query(UserGroup).filter_by(group_id=group_id,
                                    user_id=sess['user_id']).first()
    me = query(User).get(sess['user_id'])
    
    # Make sure I'm in that group (to be able to decrypt the groupkey)
    if not ug or (not ug.is_admin and not me.is_admin):
        return vaultMsg(False, "You are not admin on that group (nor global admin)")


class XMLRPCDispatcher(object):

    def _dispatch(self, request, method, params):

        params = (request, ) + params

        if method in self.registry:
            return self.registry[method](*params)

    def __init__(self):
        self.registry = {}
        self.scan(sys.modules[__name__])

    def scan(self, module):
        scanner = venusian.Scanner(registry=self.registry)
        scanner.scan(module)


class xmlrpc_method(object):
    """This decorator may be used with pyramid view callables to enable
    them to respond to XML-RPC method calls.

    If ``method`` is not supplied, then the callable name will be used
    for the method name.

    ``_depth`` may be specified when wrapping ``xmlrpc_method`` in another
    decorator. The value should reflect how many stack frames are between
    the wrapped target and ``xmlrpc_method``. Thus a decorator one level deep
    would pass in ``_depth=1``.

    This is the lazy analog to the
    :func:`~pyramid_rpc.xmlrpc.add_xmlrpc_method`` and accepts all of
    the same arguments.

    """
    def __init__(self, method=None, **kw):
        self.method = method
        self.kw = kw

    def __call__(self, wrapped):
        kw = self.kw.copy()
        kw['method'] = self.method or wrapped.__name__

        def callback(scanner, name, ob):
            scanner.registry[kw['method']] = ob


        info = venusian.attach(wrapped, callback, category='pyramid')
        if info.scope == 'class':
            # ensure that attr is set if decorating a class method
            kw.setdefault('attr', wrapped.__name__)

        kw['_info'] = info.codeinfo # fbo action_method
        return wrapped


@decorator
def authenticated_user(func, request, *args, **kwargs):
    """Aborts if user isn't authenticated.

    Timeout check done in session_errors.

    WARNING: authenticated_user READ the FIRST non-keyword argument
             (should be authtok)
    """
    cryptok = request['rpc_args'][0]
    error_msg = session_errors(request, cryptok)
    if error_msg:
        return vaultMsg(False, "Permission denied (%s)" % error_msg)

    return func(request, *args, **kwargs)


def session_errors(request, authtok):
    """ Test the session for errors

    Make sure that the session the user is trying to use is valid.

    Make the following tests:
    1. Existence: make sure the authtok has an actual session
    2. Expiration: make sure that the session is not expired
    3. Remote addr: make sure that the user is connecting from the original
                    remote addr

    Return: the error message if the session is invalid, otherwise None
    """

    error_msg = None
    if not session_exists(authtok):
        error_msg = 'session not found'

    elif session_expired(authtok):
        error_msg = 'session expired'

    elif not session_has_same_address(authtok, request):
        del(vaultSessions[authtok])
        error_msg = 'remote addr for this session is different than the original remote addr'

    if error_msg:
        return error_msg


@decorator
def authenticated_admin(func, request, *args, **kwargs):
    """Aborts if user isn't admin.

    Check authenticated_user , everything written then applies here as well.
    """
    cryptok = request['rpc_args'][0]
    error_msg = session_errors(request, cryptok)
    if error_msg:
        return vaultMsg(False, "Permission denied (%s)" % error_msg)

    sess = get_session(cryptok)

    if not sess['userobj'].is_admin:
        return vaultMsg(False, "Permission denied, admin priv. required")

    return func(request, *args, **kwargs)


@xmlrpc_method(endpoint='sflvault', method='sflvault.authenticate')
def sflvault_authenticate(request, username, cryptok):
    """Receive the *decrypted* cryptok, b64 encoded"""
    settings = request['settings']
    u = None
    db = None

    # DEPRECATED: will be removed in 0.9
    try:
        if settings['sflvault.vault.session_trust'].lower() in ['1', 'true', 't']:
            # If the session_trust parameter is true trust the session for the authentication.

            sess = None
            if not session_errors(request, cryptok):
                sess = get_session(cryptok)
            if sess:
                return vaultMsg(True, 'Authentication successful (cached)', {'authtok': cryptok})
    except KeyError:
        pass
    
    try:
        #u = meta.Session.query(User).filter_by(username=username).one()
        db = meta.Session()
        u = db.query(User).filter(User.username == username).all()[0]
    except:
        return vaultMsg(False, 'Invalid user')

    if u.logging_timeout < datetime.now():
        return vaultMsg(False, 'Login token expired. Now: %s Timeout: %s' % (datetime.now(), u.logging_timeout))

    # str() necessary, to convert buffer to string.
    if cryptok != str(u.logging_token):
        #TODO: Ask about this line.
        #raise Exception
        return vaultMsg(False, 'Authentication failed')
    else:
        newtok = b64encode(randfunc(32))
        set_session(newtok, {
            'username': username,
            'timeout': datetime.now() + timedelta(0, int(settings['sflvault.vault.session_timeout'])),
            'remote_addr': request.get('REMOTE_ADDR', None),
            'userobj': u,
            'user_id': u.id
        })
        return vaultMsg(True, 'Authentication successful', {'authtok': newtok})


@xmlrpc_method(endpoint='sflvault', method='sflvault.login')
def sflvault_login(request, username, version):
    # Require minimal client version.        
    user_version = LooseVersion(version)

    if not version or user_version < MINIMAL_CLIENT_VERSION:
        return vaultMsg(False, "Minimal client version required: '%s'. "\
                        "You announced yourself as version '%s'" % \
                        (MINIMAL_CLIENT_VERSION.vstring, version))

    # Return 'cryptok', encrypted with pubkey.
    # Save decoded version to user's db field.
    #transaction.begin()
    try:
        #u = query(User).filter_by(username=username).one()
        u = meta.Session.query(User).filter_by(username=username).one()
    except Exception, e:
        return vaultMsg(False, "User unknown: %s" % e.message)
    
    # TODO: implement throttling ?

    rnd = randfunc(32)
    # 15 seconds to complete login/authenticate round-trip.
    u.logging_timeout = datetime.now() + timedelta(0, 15)
    u.logging_token = b64encode(rnd)
    if not u.pubkey:
        return vaultMsg(False, "User %s is not set up. Run user-setup first!" % username)
    
    #a = meta.Session.query(User).filter_by(username=username).one()
    e = u.elgamal()
    cryptok = serial_elgamal_msg(e.encrypt(rnd, randfunc(32)))
    
    transaction.commit()
    #meta.Session.close()
    return vaultMsg(True, 'Authenticate please', {'cryptok': cryptok})

@xmlrpc_method(endpoint='sflvault', method='sflvault.user_add')
@authenticated_admin
def user_add(request, authtok, username, is_admin):
    try:
        setup_timeout = request['settings']['sflvault.vault.setup_timeout']
    except KeyError, e:
        setup_timeout = 300
    return vault.user_add(get_user(authtok), username, is_admin, setup_timeout=setup_timeout)

@xmlrpc_method(endpoint='sflvault', method='sflvault.user_setup')
def user_setup(request, username, pubkey):
    return vault.user_setup(username, pubkey)

@xmlrpc_method(endpoint='sflvault', method='sflvault.user_del')
@authenticated_admin
def sflvault_user_del(request, authtok, username):
    return vault.user_del(get_user(authtok), username)

@xmlrpc_method(endpoint='sflvault', method='sflvault.user_list')
@authenticated_user
def sflvault_user_list(request, authtok, groups):
    return vault.user_list(get_user(authtok), groups)

@xmlrpc_method(endpoint='sflvault', method='sflvault.machine_get')
@xmlrpc_method(endpoint='sflvault', method='sflvault.machine.get')
@authenticated_user
def sflvault_machine_get(request, authtok, machine_id):
    return vault.machine_get(machine_id)

@xmlrpc_method(endpoint='sflvault', method='sflvault.machine_put')
@authenticated_user
def sflvault_machine_put(request, authtok, machine_id, data):
    return vault.machine_put(get_user(authtok), machine_id, data)

@xmlrpc_method(endpoint='sflvault', method='sflvault.service_get')
@authenticated_user
def sflvault_service_get(request, authtok, service_id, group_id=None):
    return vault.service_get(get_user(authtok), service_id, group_id)


# si ça arrive via /jsonrpc .. on convertie en JSON en sortant
# si ça arrive via /vault/rpc .. on convertie en XML-RPC
#  XML-RPC faudrait qu'il passe simplement ses paramètres.. SAUF authtok
#  - Donc doit gérer aussi le cas du login, ou le auth-tok est requis.

#@rpc_view(method='sflvault.service_get', skip_first=False)
#def sflvault_service_get(authtok, service_id, group_id=None):

@xmlrpc_method(endpoint='sflvault', method='sflvault.service_get_tree')
@authenticated_user
def sflvault_service_get_tree(request, authtok, service_id, with_groups):
    return vault.service_get_tree(get_user(authtok), service_id)

@xmlrpc_method(endpoint='sflvault', method='sflvault.service_put')
@authenticated_user
def sflvault_service_put(request, authtok, service_id, data):
    return vault.service_put(get_user(authtok), service_id, data)


@xmlrpc_method(endpoint='sflvault', method='sflvault.search')
@authenticated_user
def sflvault_search(request,  authtok, search_query, group_ids, verbose, filters):
    if group_ids and not filters:
        filters = {'groups': group_ids}
    if group_ids and isinstance(filters, dict) and 'groups' not in filters:
        # Please don't do that, use filters instead.
        filters['groups'] = group_ids

    return vault.search(get_user(authtok), search_query, filters, verbose)

@xmlrpc_method(endpoint='sflvault', method='sflvault.service_add')
@authenticated_user
def sflvault_service_add(
        request, authtok, machine_id, parent_service_id, url, group_ids, secret, notes, metadata):
    return vault.service_add(
        get_user(authtok),
        machine_id,
        parent_service_id,
        url,
        group_ids,
        secret,
        notes,
        metadata
    )

@xmlrpc_method(endpoint='sflvault', method='sflvault.service_del')
@authenticated_admin
def sflvault_service_del(request, authtok, service_id):
    return vault.service_del(get_user(authtok), service_id)

@xmlrpc_method(endpoint='sflvault', method='sflvault.service_list')
@authenticated_user
def sflvault_service_list(request, authtok, machine_id=None, customer_id=None):
    return vault.service_list(get_user(authtok), machine_id, customer_id)

@xmlrpc_method(endpoint='sflvault', method='sflvault.machine_add')
@authenticated_user
def sflvault_machine_add(request, authtok, customer_id, name, fqdn, ip, location, notes):
    return vault.machine_add(get_user(authtok), customer_id, name, fqdn, ip, location, notes)

@xmlrpc_method(endpoint='sflvault', method='sflvault.machine_del')
@authenticated_admin
def sflvault_machine_del(request, authtok, machine_id):
    return vault.machine_del(get_user(authtok), machine_id)

@xmlrpc_method(endpoint='sflvault', method='sflvault.machine_list')
@authenticated_user
def sflvault_machine_list(request, authtok, customer_id=None):
    return vault.machine_list(get_user(authtok), customer_id)

@xmlrpc_method(endpoint='sflvault', method='sflvault.customer_get')
@xmlrpc_method(endpoint='sflvault', method='sflvault.customer.get')
@authenticated_user
def sflvault_customer_get(request, authtok, customer_id):
    return vault.customer_get(get_user(authtok), customer_id)

@xmlrpc_method(endpoint='sflvault', method='sflvault.customer_put')
@authenticated_user
def sflvault_customer_put(request, authtok, customer_id, data):
    return vault.customer_put(get_user(authtok), customer_id, data)

@xmlrpc_method(endpoint='sflvault', method='sflvault.customer_add')
@authenticated_user
def sflvault_customer_add(request, authtok, customer_name):
    return vault.customer_add(get_user(authtok), customer_name)

@xmlrpc_method(endpoint='sflvault', method='sflvault.customer_del')
@authenticated_admin
def sflvault_customer_del(request, authtok, customer_id):
    return vault.customer_del(get_user(authtok), customer_id)

@xmlrpc_method(endpoint='sflvault', method='sflvault.customer_list')
@authenticated_user
def sflvault_customer_list(request, authtok):
    return vault.customer_list()

@xmlrpc_method(endpoint='sflvault', method='sflvault.group_get')
@authenticated_user
def sflvault_group_get(request, authtok, group_id):
    return vault.group_get(get_user(authtok), group_id)

@xmlrpc_method(endpoint='sflvault', method='sflvault.group_put')
@authenticated_user
def sflvault_group_put(request, authtok, group_id, data):
    return vault.group_put(get_user(authtok), group_id, data)

@xmlrpc_method(endpoint='sflvault', method='sflvault.group_add')
@authenticated_user
def sflvault_group_add(request, authtok, group_name):
    return vault.group_add(get_user(authtok), group_name)

@xmlrpc_method(endpoint='sflvault', method='sflvault.group_del')
@authenticated_admin
def sflvault_group_del(request, authtok, group_id, delete_cascade):
    return vault.group_del(
        get_user(authtok),
        group_id,
        delete_cascade=delete_cascade
    )

@xmlrpc_method(endpoint='sflvault', method='sflvault.group_add_service')
@authenticated_user
def sflvault_group_add_service(request, authtok, group_id, service_id, symkey):
    return vault.group_add_service(get_user(authtok), group_id, service_id, symkey)

@xmlrpc_method(endpoint='sflvault', method='sflvault.group_del_service')
@authenticated_user
def sflvault_group_del_service(request, authtok, group_id, service_id):
    fail = test_group_admin(request, group_id)
    if fail:
        return fail
    return vault.group_del_service(get_user(authtok), group_id, service_id)

@xmlrpc_method(endpoint='sflvault', method='sflvault.group_add_user')
@authenticated_user
def sflvault_group_add_user(request, authtok, group_id, user, is_admin=False, cryptgroupkey=None):
    return vault.group_add_user(get_user(authtok), group_id, user, is_admin, cryptgroupkey)

@xmlrpc_method(endpoint='sflvault', method='sflvault.group_del_user')
@authenticated_user
def sflvault_group_del_user(request, authtok, group_id, user_id):
    fail = test_group_admin(request, group_id)
    if fail:
        return fail
    return vault.group_del_user(get_user(authtok), group_id, user_id)

@xmlrpc_method(endpoint='sflvault', method='sflvault.group_list')
@xmlrpc_method(endpoint='sflvault', method='sflvault.group.list')
@authenticated_user
def sflvault_group_list(request, authtok, list_users=False):
    return vault.group_list(get_user(authtok), False, list_users)

@xmlrpc_method(endpoint='sflvault', method='sflvault.service_passwd')
@authenticated_user
def sflvault_service_passwd(request, authtok, service_id, newsecret):
    return vault.service_passwd(get_user(authtok), service_id, newsecret)

#def _setup_sessions():
#    """DRY out set_session and get_session"""
#    if not hasattr(, 'vaultSessions'):
#        .vaultSessions = {}
def set_session(authtok, value):
    """Sets in 'g.vaultSessions':
    {authtok1: {'username':  , 'timeout': datetime}, authtok2: {}..}
    
    """
#   _setup_sessions();
    vaultSessions[authtok] = value


def session_exists(authtok):
    """ Return True if the session exists """
    return authtok in vaultSessions


def session_expired(authtok):
    """ Verify the expiration time of the session

    Return True if the session is still valid
    """
    # XXX: where does the SESSION_TIMEOUT come from?
    if 'timeout' not in vaultSessions[authtok]:
        vaultSessions[authtok]['timeout'] = datetime.now() + timedelta(0, SESSION_TIMEOUT)

    if vaultSessions[authtok]['timeout'] < datetime.now():
        del(vaultSessions[authtok])
        return True
    return False


def session_has_same_address(authtok, request):
    """ Verify the remote address of the user

    Return True if the address of the request is the same
    than the one this session was created for """
    if vaultSessions[authtok]['remote_addr'] != request.get('REMOTE_ADDR', 'gibberish'):
        return False
    return True


def get_user(authtok):
    """ Return the user associated with an authtok """
    session = get_session(authtok)
    if not session:
        return None
    return query(User).get(session['user_id'])

def get_session(authtok):
    """Return the values associated with a session"""

    if session_exists(authtok):
        return vaultSessions[authtok]
    return None
