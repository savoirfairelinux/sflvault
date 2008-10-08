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


# ALL THE FOLLOWING IMPORTS MOVED TO vault.py:
import xmlrpclib
#import pylons
#from pylons import request
from base64 import b64decode, b64encode
from datetime import *
import time as stdtime

from sflvault.lib.base import *
from sflvault.lib.vault import SFLvaultAccess
from sflvault.model import *

from sqlalchemy import sql, exceptions

log = logging.getLogger(__name__)


# MOVED TO vault.py:
SETUP_TIMEOUT = 300
SESSION_TIMEOUT = 300


##
## See: http://wiki.pylonshq.com/display/pylonsdocs/Using+the+XMLRPCController
##
class XmlrpcController(XMLRPCController):
    """This controller is required to call model.Session.remove()
    after each call, otherwise, junk remains in the SQLAlchemy caches."""
    
    def __call__(self, environ, start_response):
        """Invoke the Controller"""
        # WSGIController.__call__ dispatches to the Controller method
        # the request is routed to. This routing information is
        # available in environ['pylons.routes_dict']
        
        self.vault = SFLvaultAccess()
        
        try:
            return XMLRPCController.__call__(self, environ, start_response)
        finally:
            model.meta.Session.remove()
    
    allow_none = True # Enable marshalling of None values through XMLRPC.

    def sflvault_login(self, username):
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
                                 'timeout': datetime.now() + timedelta(0, SESSION_TIMEOUT),
                                 'userobj': u,
                                 'user_id': u.id
                                 })

            return vaultMsg(True, 'Authentication successful', {'authtok': newtok})


    def sflvault_setup(self, username, pubkey):

        # First, remove ALL users that have waiting_setup expired, where
        # waiting_setup isn't NULL.
        #meta.Session.delete(query(User).filter(User.waiting_setup != None).filter(User.waiting_setup < datetime.now()))
        #raise RuntimeError
        cnt = query(User).count()
        
        u = query(User).filter_by(username=username).first()


        if (cnt):
            if (not u):
                return vaultMsg(False, 'No such user %s' % username)
        
            if (u.setup_expired()):
                return vaultMsg(False, 'Setup expired for user %s' % username)

        # Ok, let's save the things and reset waiting_setup.
        u.waiting_setup = None
        u.pubkey = pubkey

        meta.Session.commit()

        return vaultMsg(True, 'User setup complete for %s' % username)


    @authenticated_user
    def sflvault_show(self, authtok, service_id):
        self.vault.myself_id = self.sess['user_id']
        return self.vault.show(service_id)

    @authenticated_user
    def sflvault_search(self, authtok, search_query, verbose=False):
        return self.vault.search(search_query, verbose)

    @authenticated_admin
    def sflvault_adduser(self, authtok, username, is_admin):
        return self.vault.add_user(username, is_admin)

    @authenticated_admin
    def sflvault_grant(self, authtok, user, group_ids):
        self.vault.myself_id = self.sess['user_id']
        return self.vault.grant(user, group_ids)

    @authenticated_admin
    def sflvault_grantupdate(self, authtok, user, ciphers):
        return self.vault.grant_update(user, ciphers)

    @authenticated_admin
    def sflvault_revoke(self, authtok, user, group_ids):
        return self.vault.revoke(user, group_ids)
        
    @authenticated_admin
    def sflvault_analyze(self, authtok, user):
        return self.vault.analyze(user)

    @authenticated_user
    def sflvault_addmachine(self, authtok, customer_id, name, fqdn, ip,
                            location, notes):
        return self.vault.add_machine(customer_id, name, fqdn, ip,
                                      location, notes)

    @authenticated_user
    def sflvault_addservice(self, authtok, machine_id, parent_service_id, url,
                            group_ids, secret, notes):
        self.vault.myself_id = self.sess['user_id']
        return self.vault.add_service(machine_id, parent_service_id, url,
                                      group_ids, secret, notes)
        
    @authenticated_admin
    def sflvault_deluser(self, authtok, user):

        # Get user
        try:
            usr = model.get_user(user)
        except LookupError, e:
            return vaultMsg(False, str(e))

        meta.Session.execute(model.usergroups_table.delete(user_id=usr.id))
        meta.Session.execute(model.userciphers_table.delete(user_id=usr.id))
        
        meta.Session.delete(usr)
        meta.Session.commit()

        return vaultMsg(True, "User successfully deleted")


    @authenticated_admin
    def sflvault_delcustomer(self, authtok, customer_id):
        # Get customer
        cust = query(model.Customer).options(model.eagerload('machines'))\
                                    .get(int(customer_id))

        if not cust:
            return vaultMsg(True, "No such customer: c#%s" % customer_id)

        # Get all the services that will be deleted
        servs = query(model.Service).join(['machine', 'customer']) \
                     .filter(model.Customer.id == customer_id) \
                     .all()
        servs_ids = [s.id for s in servs]

        # Make sure no service is child of this one
        childs = query(model.Service) \
                     .filter(model.Service.parent_service_id.in_(servs_ids))\
                     .all()

        # Don't bother for parents/childs if we're going to delete it anyway.
        remnants = list(set(childs).difference(set(servs)))

        if len(remnants):
            # There are still some childs left, we can't delete this one.
            retval = []
            for x in remnants:
                retval.append({'id': x.id, 'url': x.url})
                
            return vaultMsg(False, "Services still child of this customer's machine's services",
                            {'childs': retval})

        # Delete all related user-ciphers
        d = sql.delete(model.userciphers_table) \
               .where(model.userciphers_table.c.service_id.in_(servs_ids))
        # Delete the services related to customer_id's machines
        d2 = sql.delete(model.services_table) \
                .where(model.services_table.c.id.in_(servs_ids))
        # Delete the machines related to customer_id
        mach_ids = [m.id for m in cust.machines]
        d3 = sql.delete(model.machines_table) \
                .where(model.machines_table.c.id.in_(mach_ids))
        # Delete the customer
        d4 = sql.delete(model.customers_table) \
                .where(model.customers_table.c.id == customer_id)

        meta.Session.execute(d)
        meta.Session.execute(d2)
        meta.Session.execute(d3)
        meta.Session.execute(d4)
        
        meta.Session.commit()

        return vaultMsg(True,
                        'Deleted customer c#%s successfully' % customer_id)



    @authenticated_admin
    def sflvault_delmachine(self, authtok, machine_id):
        # Get machine
        machine = query(model.Machine).get(int(machine_id))

        if not machine:
            return vaultMsg(True, "No such machine: m#%s" % machine_id)

        # Get all the services that will be deleted
        servs = query(model.Service).join('machine') \
                     .filter(model.Machine.id == machine_id).all()
        servs_ids = [s.id for s in servs]

        # Make sure no service is child of this one
        childs = query(model.Service) \
                     .filter(model.Service.parent_service_id.in_(servs_ids))\
                     .all()

        # Don't bother for parents/childs if we're going to delete it anyway.
        remnants = list(set(childs).difference(set(servs)))

        if len(remnants):
            # There are still some childs left, we can't delete this one.
            retval = []
            for x in remnants:
                retval.append({'id': x.id, 'url': x.url})
                
            return vaultMsg(False, "Services still child of this machine's services",
                            {'childs': retval})


        # Delete all related user-ciphers
        d = sql.delete(model.userciphers_table) \
               .where(model.userciphers_table.c.service_id.in_(servs_ids))
        # Delete the services related to machine_id
        d2 = sql.delete(model.services_table) \
                .where(model.services_table.c.id.in_(servs_ids))
        # Delete the machine
        d3 = sql.delete(model.machines_table) \
                .where(model.machines_table.c.id == machine_id)

        meta.Session.execute(d)
        meta.Session.execute(d2)
        meta.Session.execute(d3)
        
        meta.Session.commit()

        return vaultMsg(True, 'Deleted machine m#%s successfully' % machine_id)


    @authenticated_admin
    def sflvault_delservice(self, authtok, service_id):
        """Delete a service, making sure no other child remains attached."""
        # Integerize
        service_id = int(service_id)
        # Get service
        serv = query(model.Service).get(int(service_id))

        if not serv:
            return vaultMsg(True, "No such service: s#%s" % service_id)

        # Make sure no service is child of this one
        childs = query(model.Service).filter_by(parent_service_id=service_id).all()

        if len(childs):
            # There are still some childs left, we can't delete this one.
            retval = []
            for x in childs:
                retval.append({'id': x.id, 'url': x.url})
                
            return vaultMsg(False, 'Services still child of this service',
                            {'childs': retval})
        
        # Delete all related user-ciphers
        d = sql.delete(model.userciphers_table) \
               .where(model.userciphers_table.c.service_id == service_id)
        # Delete the service
        d2 = sql.delete(services_table) \
                .where(services_table.c.id == service_id)
        
        meta.Session.execute(d)
        meta.Session.execute(d2)
        meta.Session.commit()

        return vaultMsg(True, 'Deleted service s#%s successfully' % service_id)


    @authenticated_user
    def sflvault_addcustomer(self, authtok, customer_name):
        nc = Customer()
        nc.name = customer_name
        nc.created_time = datetime.now()
        nc.created_user = self.sess['username']

        meta.Session.save(nc)
        
        meta.Session.commit()

        return vaultMsg(True, 'Customer added', {'customer_id': nc.id})


    @authenticated_user
    def sflvault_listcustomers(self, authtok):
        lst = query(Customer).all()

        out = []
        for x in lst:
            nx = {'id': x.id, 'name': x.name}
            out.append(nx)

        return vaultMsg(True, 'Here is the customer list', {'list': out})


    @authenticated_admin
    def sflvault_addgroup(self, authtok, group_name):

        ng = Group()

        ng.name = group_name

        meta.Session.save(ng)

        meta.Session.commit()

        return vaultMsg(True, "Added group '%s'" % ng.name,
                        {'name': ng.name, 'group_id': int(ng.id)})


    @authenticated_user
    def sflvault_listgroups(self, authtok):
        groups = query(Group).group_by(Group.name).all()

        out = []
        for x in groups:
            out.append({'id': x.id, 'name': x.name})

        return vaultMsg(True, 'Here is the list of groups', {'list': out})


    @authenticated_user
    def sflvault_listmachines(self, authtok):
        lst = query(Machine).all()

        out = []
        for x in lst:
            nx = {'id': x.id, 'name': x.name, 'fqdn': x.fqdn, 'ip': x.ip,
                  'location': x.location, 'notes': x.notes,
                  'customer_id': x.customer_id,
                  'customer_name': x.customer.name}
            out.append(nx)

        return vaultMsg(True, "Here is the machines list", {'list': out})
    

    @authenticated_user
    def sflvault_listusers(self, authtok):
        lst = query(User).all()

        out = []
        for x in lst:
            # perhaps add the pubkey ?
            if x.created_time:
                stmp = xmlrpclib.DateTime(x.created_time)
            else:
                stmp = 0
                
            nx = {'id': x.id, 'username': x.username,
                  'created_stamp': stmp,
                  'is_admin': x.is_admin,
                  'setup_expired': x.setup_expired(),
                  'waiting_setup': bool(x.waiting_setup)}
            out.append(nx)

        # Can use: datetime.fromtimestamp(x.created_stamp)
        # to get a datetime object back from the x.created_time
        return vaultMsg(True, "Here is the user list", {'list': out})
