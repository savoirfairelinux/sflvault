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

import logging
from distutils.version import LooseVersion


MINIMAL_CLIENT_VERSION = LooseVersion('0.7.6')


# ALL THE FOLLOWING IMPORTS MOVED TO vault.py:
import xmlrpclib
from pylons import request
from base64 import b64encode
from datetime import *
from decorator import decorator
from pylons.controllers.xmlrpc import xmlrpc_fault

from sflvault.lib.base import *
from sflvault.lib.vault import SFLvaultAccess
from sflvault.model import *

from sqlalchemy import sql, exceptions

log = logging.getLogger(__name__)


#
# Permissions decorators for XML-RPC calls
#

def _authenticated_user_first(self, *args, **kwargs):
    """DRYed authenticated_user to skip repetition in authenticated_admin"""
    s = get_session(args[0])

    if not s:
        return vaultMsg(False, "Permission denied")

    self.sess = s

    if hasattr(self, 'vault'):
        if 'user_id' in self.sess:
            self.vault.myself_id = self.sess['user_id']
        if 'username' in self.sess:
            self.vault.myself_username = self.sess['username']


@decorator
def authenticated_user(func, self, *args, **kwargs):
    """Aborts if user isn't authenticated.

    Timeout check done in get_session.

    WARNING: authenticated_user READ the FIRST non-keyword argument
             (should be authtok)
    """
    ret = _authenticated_user_first(self, *args, **kwargs)
    if ret:
        return ret

    return func(self, *args, **kwargs)

@decorator
def authenticated_admin(func, self, *args, **kwargs):
    """Aborts if user isn't admin.

    Check authenticated_user , everything written then applies here as well.
    """
    ret = _authenticated_user_first(self, *args, **kwargs)
    if ret:
        return ret

    if not self.sess['userobj'].is_admin:
        return vaultMsg(False, "Permission denied, admin priv. required")

    return func(self, *args, **kwargs)


##
## See: http://wiki.pylonshq.com/display/pylonsdocs/Using+the+XMLRPCController
##
class XmlrpcController(XMLRPCController):
    """This controller is required to call model.Session.remove()
    after each call, otherwise, junk remains in the SQLAlchemy caches."""

    allow_none = True # Enable marshalling of None values through XMLRPC.
    
    def __call__(self, environ, start_response):
        """Invoke the Controller"""
        self.vault = SFLvaultAccess()
        self.vault.setup_timeout = config['sflvault.vault.setup_timeout']

        try:
            return XMLRPCController.__call__(self, environ, start_response)
        # could be useful at some point:
        #except VaultError, e:
        #    print "ASLDJLASDJLASKJDKASJLD"
        #    return xmlrpc_fault(0, e.message)(environ, start_response)
        finally:
            model.meta.Session.remove()
    
    def sflvault_login(self, username, version=None):
        # Require minimal client version.        
        user_version = LooseVersion(version)
        if not version or user_version < MINIMAL_CLIENT_VERSION:
            return vaultMsg(False, "Minimal client version required: '%s'. "\
                            "You announced yourself as version '%s'" % \
                            (MINIMAL_CLIENT_VERSION.vstring, version))

        # Return 'cryptok', encrypted with pubkey.
        # Save decoded version to user's db field.
        try:
            u = query(User).filter_by(username=username).one()
        except Exception, e:
            return vaultMsg(False, "User unknown: %s" % e.message )
        
        # TODO: implement throttling ?

        rnd = randfunc(32)
        # 15 seconds to complete login/authenticate round-trip.
        u.logging_timeout = datetime.now() + timedelta(0, 15)
        u.logging_token = b64encode(rnd)

        meta.Session.flush()
        meta.Session.commit()

        e = u.elgamal()
        cryptok = serial_elgamal_msg(e.encrypt(rnd, randfunc(32)))
        return vaultMsg(True, 'Authenticate please', {'cryptok': cryptok})

    def sflvault_authenticate(self, username, cryptok):
        """Receive the *decrypted* cryptok, b64 encoded"""

        u = None
        try:
            u = query(User).filter_by(username=username).one()
        except:
            return vaultMsg(False, 'Invalid user')

        if u.logging_timeout < datetime.now():
            return vaultMsg(False, 'Login token expired. Now: %s Timeout: %s' % (datetime.now(), u.logging_timeout))

        # str() necessary, to convert buffer to string.
        if cryptok != str(u.logging_token):
            return vaultMsg(False, 'Authentication failed')
        else:
            newtok = b64encode(randfunc(32))
            set_session(newtok, {'username': username,
                                 'timeout': datetime.now() + timedelta(0, int(config['sflvault.vault.session_timeout'])),
                                 'remote_addr': request.environ.get('REMOTE_ADDR', None),
                                 'userobj': u,
                                 'user_id': u.id
                                 })

            return vaultMsg(True, 'Authentication successful', {'authtok': newtok})


    def sflvault_user_setup(self, username, pubkey):
        return self.vault.user_setup(username, pubkey)

    @authenticated_admin
    def sflvault_user_add(self, authtok, username, is_admin):
        return self.vault.user_add(username, is_admin)

    @authenticated_admin
    def sflvault_user_del(self, authtok, user):
        return self.vault.user_del(user)

    @authenticated_user
    def sflvault_user_list(self, authtok, groups=False):
        return self.vault.user_list(groups)

    @authenticated_user
    def sflvault_machine_get(self, authtok, machine_id):
        return self.vault.machine_get(machine_id)

    @authenticated_user
    def sflvault_machine_put(self, authtok, machine_id, data):
        return self.vault.machine_put(machine_id, data)

    @authenticated_user
    def sflvault_service_get(self, authtok, service_id, group_id=None):
        return self.vault.service_get(service_id, group_id)

    @authenticated_user
    def sflvault_service_get_tree(self, authtok, service_id, with_groups=False):
        return self.vault.service_get_tree(service_id, with_groups)

    @authenticated_user
    def sflvault_service_put(self, authtok, service_id, data):
        # 'user_id' required in session.
        # TODO: verify I had access to the service previously.
        req = sql.join(servicegroups_table, usergroups_table,
                       ServiceGroup.group_id==UserGroup.group_id) \
                 .join(users_table, User.id==UserGroup.user_id) \
                 .select() \
                 .where(User.id==self.sess['user_id']) \
                 .where(ServiceGroup.service_id==service_id)
        res = list(meta.Session.execute(req))
        if not res:
            return vaultMsg(False, "You don't have access to that service.")
        else:
            return self.vault.service_put(service_id, data)

    @authenticated_user
    def sflvault_search(self, authtok, search_query, group_ids=None,
                        verbose=False, filters=None):
        if group_ids and not filters:
            filters = {'groups': group_ids}
        if group_ids and isinstance(filters, dict) and 'groups' not in filters:
            # Please don't do that, use filters instead.
            filters['groups'] = group_ids
        return self.vault.search(search_query, filters, verbose)

    @authenticated_user
    def sflvault_service_add(self, authtok, machine_id, parent_service_id, url,
                             group_ids, secret, notes, metadata=None):
        return self.vault.service_add(machine_id, parent_service_id, url,
                                      group_ids, secret, notes, metadata)
        
    @authenticated_admin
    def sflvault_service_del(self, authtok, service_id):
        return self.vault.service_del(service_id)

    @authenticated_user
    def sflvault_service_list(self, authtok, machine_id=None, customer_id=None):
        return self.vault.service_list(machine_id, customer_id)

    @authenticated_user
    def sflvault_machine_add(self, authtok, customer_id, name, fqdn, ip,
                             location, notes):
        return self.vault.machine_add(customer_id, name, fqdn, ip,
                                      location, notes)

    @authenticated_admin
    def sflvault_machine_del(self, authtok, machine_id):
        return self.vault.machine_del(machine_id)

    @authenticated_user
    def sflvault_machine_list(self, authtok, customer_id=None):
        return self.vault.machine_list(customer_id)

    @authenticated_user
    def sflvault_customer_get(self, authtok, customer_id):
        return self.vault.customer_get(customer_id)

    @authenticated_user
    def sflvault_customer_put(self, authtok, customer_id, data):
        return self.vault.customer_put(customer_id, data)

    @authenticated_user
    def sflvault_customer_add(self, authtok, customer_name):
        return self.vault.customer_add(customer_name)

    @authenticated_admin
    def sflvault_customer_del(self, authtok, customer_id):
        return self.vault.customer_del(customer_id)

    @authenticated_user
    def sflvault_customer_list(self, authtok):
        return self.vault.customer_list()

    @authenticated_user
    def sflvault_group_get(self, authtok, group_id):
        return self.vault.group_get(group_id)

    @authenticated_user
    def sflvault_group_put(self, authtok, group_id, data):
        return self.vault.group_put(group_id, data)

    @authenticated_user
    def sflvault_group_add(self, authtok, group_name):
        return self.vault.group_add(group_name)

    @authenticated_admin
    def sflvault_group_del(self, authtok, group_id):
        return self.vault.group_del(group_id)

    @authenticated_user
    def sflvault_group_add_service(self, authtok, group_id, service_id, symkey):
        return self.vault.group_add_service(group_id, service_id, symkey)

    @authenticated_user
    def sflvault_group_del_service(self, authtok, group_id, service_id):
        fail = self._test_group_admin(group_id)
        if fail:
            return fail
                
        return self.vault.group_del_service(group_id, service_id)

    @authenticated_user
    def sflvault_group_add_user(self, authtok, group_id, user, is_admin=False,
                                cryptgroupkey=None):
        return self.vault.group_add_user(group_id, user, is_admin,
                                         cryptgroupkey)

    @authenticated_user
    def sflvault_group_del_user(self, authtok, group_id, user):
        fail = self._test_group_admin(group_id)
        if fail:
            return fail
        return self.vault.group_del_user(group_id, user)

    @authenticated_user
    def sflvault_group_list(self, authtok, list_users=False):
        return self.vault.group_list(False, list_users)

    @authenticated_user
    def sflvault_service_passwd(self, authtok, service_id, newsecret):
        return self.vault.service_passwd(service_id, newsecret)

    def _test_group_admin(self, group_id):
        if not query(Group).filter_by(id=group_id).first():
            return vaultMsg(False, "Group not found: %s" % str(e))

        # Verify if I'm is_admin on that group
        ug = query(UserGroup).filter_by(group_id=group_id,
                                        user_id=self.sess['user_id']).first()
        me = query(User).get(self.sess['user_id'])
        
        # Make sure I'm in that group (to be able to decrypt the groupkey)
        if not ug or (not ug.is_admin and not me.is_admin):
            return vaultMsg(False, "You are not admin on that group (nor global admin)")
        



