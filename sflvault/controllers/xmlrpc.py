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
        """Receive a user and ciphers to be stored into the database.

        user - either username, or user_id
        ciphers - hash composed of 'id' (service_id) and encrypted
                  'cryptsymkey'.
        """

        # Get user, and relations
        try:
            usr = model.get_user(user)
        except LookupError, e:
            return vaultMsg(False, str(e))

        
        hisid = usr.id
        usrci = query(Usercipher).filter_by(user_id=hisid) \
                    .filter(Usercipher.service_id.in_( \
                                                [s['id'] for s in ciphers])) \
                    .all()

        # Get a list of all service_id he already has
        usr_services = [uc.service_id for uc in usrci]

        for ci in ciphers:
            if not isinstance(ci, dict) or not ci.has_key('id') \
                                         or not ci.has_key('cryptsymkey'):
                return vaultMsg(False, "Malformed ciphers (must be dicts, with 'id' and 'cryptsymkey')");


            if ci['id'] in usr_services:
                # Hey, don't send me stuff I already have!
                # TODO: log this event, raise an error ??
                #continue
                return vaultMsg(False, "Encrypted ciphers already present for user %s" % usr.username)

            nu = Usercipher()
            nu.user_id = hisid
            nu.service_id = ci['id']
            nu.cryptsymkey = ci['cryptsymkey']

            meta.Session.save(nu)

        # Loop received ciphers, make sure they aren't already in, and add them
        meta.Session.commit()

        # TODO: Log this event somewhere! thanks :)

        return vaultMsg(True, "Privileges granted successfully")



    @authenticated_admin
    def sflvault_revoke(self, authtok, user, group_ids):
        """Revoke permisssions (and destroy ciphers for user) of a group
        for a user"""
        
        # Get user, and relations
        try:
            usr = model.get_user(user, 'groups.services')
        except LookupError, e:
            return vaultMsg(False, str(e))

        # Get groups
        try:
            groups, group_ids = model.get_groups_list(group_ids)
        except ValueError, e:
            return vaultMsg(False, str(e))

        
        remgrps = set(groups)
        mygrps = set(usr.groups)
        
        # Remove groups
        usr.groups = list(mygrps.difference(remgrps))
        
        # Pull the groups from the DB, TODO: DRY
        groups = query(Group).filter(Group.id.in_(group_ids)).all()

        # Remove all user-ciphers for services in those groups
        # From which groups ?
        rmdgrps = mygrps.intersection(remgrps)

        # Get list of service_id:
        service_ids = []
        for g in rmdgrps:
            service_ids.extend([srv.id for srv in g.services])

        # TODO: remove all user-cipher for user `usr` where service.id matches
        # service_ids
        ciphers = usr.userciphers

        newciphers = [ciph for ciph in ciphers
                      if ciph.service_id in service_ids]
        
        #for ciph in ciphers:
        # TODO: terminate that, is STILL DOESN'T REMOVE THE CIPHERS!
        # TODO: verify that the cipher is still available somewhere before
        #       removing it, otherwise some services may be rendered useless.
        #       of the password could be lost.
        
        # TODO(future): Make sure when you remove a Usercipher for a service
        # that matches the specified groups, that you keep it if another group
        # that you are not removing still exists for the user.

        return vaultMsg(True, "Revoked stuff", {'service_ids': service_ids})



    @authenticated_admin
    def sflvault_analyze(self, authtok, user):
        """Return a report of the left-overs (if any) of ciphers on a certain
        user. Report the number of missing ciphers, the amount to be removed,
        etc.."""

        # Get user, and relations
        try:
            usr = model.get_user(user, 'userciphers.service.group')
        except LookupError, e:
            return vaultMsg(False, str(e))

        # All services user should have access to
        all_servs = usr.services
            
        # Services for which user has already ciphers
        ciph_servs = [uc.service for uc in usr.userciphers \
                      if uc.service is not None]

        # Remove all userciphers that point to no service (uc.service == None)
        cleaned_ciphers = 0
        for uc in usr2.userciphers:
            if uc.service is None:
                cleaned_ciphers += 1
                meta.Session.delete(uc)
        
        all_set = set(all_servs)
        ciph_set = set(ciph_servs)

        common_set = all_set.intersection(ciph_set)

        missing_set = all_set.difference(ciph_set)
        over_set = ciph_set.difference(all_set)

        #REMOVAL: These can't work anymore with many-to-many service-group
        #         relation. We'll have to find another way to do it.
        #   TODO: probably, have a -c|--clean option, that would just
        #         remove unnecessary stuff, and a -g|--grant that would
        #         start a grantupdate process for those things.
        #
        # List groups that are missing (to be re-granted)
        #missing_groups = {}
        #for m in missing_set:
        #    missing_groups[str(m.group.id)] = m.group.name
        #
        # List groups that are over (to be revoked)
        #over_groups = {}
        #for o in over_set:
        #    # When there is a 'None' in here
        #    over_groups[str(o.group.id)] = o.group.name

        # Finish clean up..
        meta.Session.commit()

        # Generate report:

        report = {}
        report['total_services'] = len(all_set)
        report['total_ciphers'] = len(ciph_set)
        report['missing_ciphers'] = len(missing_set)
        #report['missing_groups'] = missing_groups
        report['over_ciphers'] = len(over_set)
        #report['over_groups'] = over_groups
        report['cleaned_ciphers'] = cleaned_ciphers

        return vaultMsg(True, "Analysis report for user %s" % usr1.username,
                        report)


    @authenticated_user
    def sflvault_addmachine(self, authtok, customer_id, name, fqdn, ip,
                            location, notes):

        nm = Machine()
        nm.customer_id = int(customer_id)
        nm.created_time = datetime.now()
        if not name:
            return vaultMsg(False, "Missing requierd argument: name")
        nm.name = name
        nm.fqdn = fqdn or ''
        nm.ip = ip or ''
        nm.location = location or ''
        nm.notes = notes or ''

        meta.Session.save(nm)
        
        meta.Session.commit()

        return vaultMsg(True, "Machine added.", {'machine_id': nm.id})


    @authenticated_user
    def sflvault_addservice(self, authtok, machine_id, parent_service_id, url,
                            group_ids, secret, notes):
        # Get groups
        try:
            groups, group_ids = model.get_groups_list(group_ids)
        except ValueError, e:
            return vaultMsg(False, str(e))
        
        # TODO: centralise the grant and users matching service resolution.

        # Make sure the parent service exists, if specified
        if parent_service_id:
            try:
                parent = query(Service).get(parent_service_id)
            except:
                return vaultMsg(False, "No such parent service ID.",
                                {'parent_service_id': parent_service_id})


        # Add service effectively..
        ns = Service()
        ns.machine_id = int(machine_id)
        ns.parent_service_id = parent_service_id or None
        ns.url = url
        ns.groups = groups
        # seckey is the AES256 symmetric key, to be encrypted for each user.
        (seckey, ciphertext) = encrypt_secret(secret)
        ns.secret = ciphertext
        ns.secret_last_modified = datetime.now()
        ns.notes = notes

        meta.Session.save(ns)

        meta.Session.commit()


        # Get all users from the group_ids, and all admins and the requestor.
        encusers = []
        admusers = query(User).filter_by(is_admin=True).all()
        myselfuser = query(User).get(self.sess['user_id'])

        for grp in groups:
            encusers.extend(grp.users)
        for adm in admusers:
            encusers.append(adm)
        encusers.append(myselfuser)
                
        ## TODO: move all that to centralised 'save_service_password'
        ## that can be used on add-service calls and also on change-password
        ## calls

        userlist = []
        for usr in set(encusers): # take out doubles..
            # pubkey required to encrypt for user
            if not usr.pubkey:
                continue

            # Encode for that user, store in UserCiphers
            nu = Usercipher()
            nu.service_id = ns.id
            nu.user_id = usr.id

            eg = usr.elgamal()
            nu.cryptsymkey = serial_elgamal_msg(eg.encrypt(seckey,
                                                           randfunc(32)))
            del(eg)

            meta.Session.save(nu)
            
            userlist.append(usr.username) # To return listing.

        meta.Session.commit()

        del(seckey)

        return vaultMsg(True, "Service added.", {'service_id': ns.id,
                                                 'encrypted_for': userlist})

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
