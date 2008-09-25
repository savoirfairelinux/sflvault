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

import xmlrpclib
#import pylons
#from pylons import request
from base64 import b64decode, b64encode
from datetime import *
import time as stdtime

from sflvault.lib.base import *
from sflvault.model import *

from sqlalchemy import sql

log = logging.getLogger(__name__)

#
# Configuration
#
# TODO: make those configurable
SETUP_TIMEOUT = 300
SESSION_TIMEOUT = 300




##
## See: http://wiki.pylonshq.com/display/pylonsdocs/Using+the+XMLRPCController
##
class XmlrpcController(MyXMLRPCController):
    """All XML-RPC calls to control and query the Vault"""
    
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
    def sflvault_show(self, authtok, vid):
        """Get the specified service ID and return the hierarchy to connect to it."""
        try:
            s = query(Service).filter_by(id=vid).options(model.eagerload('group')).one()
        except Exception, e:
            return vaultMsg(False, "Service not found: %s" % e.message)

        out = []
        while True:
            ucipher = query(Usercipher).filter_by(service_id=s.id, user_id=self.sess['userobj'].id).first()
            if ucipher and ucipher.cryptsymkey:
                cipher = ucipher.cryptsymkey
            else:
                cipher = ''

            out.append({'id': s.id,
                        'url': s.url,
                        'group': s.group.name or '',
                        'secret': s.secret,
                        'usercipher': cipher,
                        'secret_last_modified': s.secret_last_modified,
                        'metadata': s.metadata or '',
                        'notes': s.notes or ''})

            if not s.parent:
                break

            # Load the parent...
            s = s.parent

            # check if we're not in an infinite loop!
            if s.id in [x['id'] for x in out]:
                return vaultMsg(False, "Circular references of parent services, aborting.")

        out.reverse()

        return vaultMsg(True, "Here are the services", {'services': out})


    @authenticated_user
    def sflvault_search(self, authtok, search_query, verbose=False):
        """Do the search, and return the result tree."""
        # TODO: narrow down search (instead of all(), doh!)
        cs = query(Customer).all()
        ms = query(Machine).all()
        ss = query(Service).all()

        search = model.search_query(search_query, verbose)


        # Quick helper funcs, to create the hierarchical 'out' structure.
        def set_customer(out, c):
            if out.has_key(str(c.customers_id)):
                return
            out[str(c.customers_id)] = {'name': c.customers_name,
                                        'machines': {}}
            
        def set_machine(subout, m):
            if subout.has_key(str(m.machines_id)):
                return
            subout[str(m.machines_id)] = {'name': m.machines_name,
                            'fqdn': m.machines_fqdn or '',
                            'ip': m.machines_ip or '',
                            'location': m.machines_location or '',
                            'notes': m.machines_notes or '',
                            'services': {}}
            
        def set_service(subsubout, s):
            subsubout[str(s.services_id)] = {'url': s.services_url,
                         #TODO: make sure groups goes through correctly
                         'group': s.groups_name or '',
                         'parent_service_id': s.services_parent_service_id \
                                              or '',
                         'metadata': s.services_metadata or '',
                         'notes': s.services_notes or ''}

        out = {}
        # Loop services, setup machines and customers first.
        for x in search:
            # Setup customer dans le out, pour le service
            set_customer(out, x)
            set_machine(out[str(x.customers_id)]['machines'], x)
            set_service(out[str(x.customers_id)]['machines'] \
                            [str(x.machines_id)]['services'], x)


        # Return 'out', in a nicely structured hierarchical form.
        return vaultMsg(True, "Here are the search results", {'results': out})
        

    @authenticated_admin
    def sflvault_adduser(self, authtok, username, admin):

        usr = query(User).filter_by(username=username).first()

        msg = ''
        if usr == None:
            # New user
            usr = User()
            usr.waiting_setup =  datetime.now() + timedelta(0, SETUP_TIMEOUT)
            usr.username = username
            usr.is_admin = bool(admin)
            usr.created_time = datetime.now()

            meta.Session.save(usr)
            
            msg = 'added'
        elif usr.waiting_setup:
            if usr.waiting_setup < datetime.now():
                # Verify if it's a waiting_setup user that has expired.
                usr.waiting_setup = datetime.now() + \
                                    timedelta(0, SETUP_TIMEOUT)
            
                msg = 'updated (had setup timeout expired)'
            else:
                return vaultMsg(False, "User %s is waiting for setup" % \
                                username)
        else:
            return vaultMsg(False, 'User %s already exists.' % username)
        
        meta.Session.commit()

        return vaultMsg(True, '%s %s. User has a delay of %d seconds to invoke a "setup" command' % \
                        (admin and 'Admin user' or 'User',
                         msg, SETUP_TIMEOUT), {'user_id': usr.id})


    @authenticated_admin
    def sflvault_grant(self, authtok, user, group_ids):
        """Grant privileges to a user, for certain groups.

        user - either a numeric user_id, or a username
        group_ids - list of numeric `group_id`s or a single group_id
        """
        # Get user, and relations
        try:
            usr = model.get_user(user)
        except LookupError, e:
            return vaultMsg(False, str(e))


        # TODO: implement the service in multiple groups behavior.


        # Get groups
        try:
            groups, group_ids = model.get_groups_list(group_ids)
        except ValueError, e:
            return vaultMsg(False, str(e))
        

        # Only in those groups
        srvs = query(Service).filter(Service.group_id.in_(group_ids)).all()

        # Grab mine and his Userciphers, we're going to fill in the gap
        hisid = usr.id
        myid = self.sess['userobj'].id
        usrci = query(Usercipher) \
                    .filter(Usercipher.user_id.in_([hisid, myid])) \
                    .filter(Usercipher.service_id.in_([s.id for s in srvs])) \
                    .all()

        mine = {}
        his = {}
        for uc in usrci:
            if uc.user_id == myid:
                mine[uc.service_id] = uc
            elif uc.user_id == hisid:
                his[uc.service_id] = uc
            else:
                raise Exception("We didn't ask for those! We should never get there")

        # Now find the missing Ciphers for that user
        lst = []
        for ucid in mine.keys():

            # If he already has that Cipher..
            if his.has_key(ucid):
                continue

            uc = mine[ucid]
            
            item = {'id': uc.service_id,
                    'cryptsymkey': uc.cryptsymkey}
            lst.append(item)

        # Check if user has already access to groups
        add_groupset = set(groups)
        his_groupset = set(usr.groups)
        add_groups = add_groupset.difference(his_groupset)
        has_groups = his_groupset.intersection(his_groupset)

        # Just generate the message..
        msg = []
        if len(add_groups):
            txt_groups = ', '.join([g.name for g in add_groups])
            msg.append("Added groups: %s" % txt_groups)
        if len(has_groups):
            txt_groups = ', '.join([g.name for g in has_groups])
            msg.append("Already was in group: %s" % txt_groups)


        # Add groups that weren't there.
        usr.groups.extend(list(add_groups))
        
        meta.Session.commit()

        msg.append("waiting for encryption round-trip" if len(lst) else \
                   "no round-trip required")
                   
        return vaultMsg(True, ', '.join(msg),
                        {'user_pubkey': usr.pubkey,
                         'user_id': usr.id,
                         'ciphers': lst})
  

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
            usr1 = model.get_user(user, 'groups.services')
            usr2 = model.get_user(user, 'userciphers.service.group')
        except LookupError, e:
            return vaultMsg(False, str(e))


        # All services user should have access to
        all_servs = []
        for g in usr1.groups:
            all_servs.extend(g.services)
            
        # Services for which user has already ciphers
        ciph_servs = [uc.service for uc in usr2.userciphers \
                      if uc.service is not None]

        # TODO: remove all userciphers that point to no service
        #       (uc.service == None)
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

        # List groups that are missing (to be re-granted)
        missing_groups = {}
        for m in missing_set:
            missing_groups[str(m.group.id)] = m.group.name

        # List groups that are over (to be revoked)
        over_groups = {}
        for o in over_set:
            # When there is a 'None' in here
            over_groups[str(o.group.id)] = o.group.name

        # Finish clean up..
        meta.Session.commit()

        # Generate report:

        report = {}
        report['total_services'] = len(all_set)
        report['total_ciphers'] = len(ciph_set)
        report['missing_ciphers'] = len(missing_set)
        report['missing_groups'] = missing_groups
        report['over_ciphers'] = len(over_set)
        report['over_groups'] = over_groups
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
                            group_id, secret, notes):
        # TODO: accept group_ids (list of groups) to put the service in
        # multiple groups.

        # TODO: centralise the grant and users matching service resolution.

        # parent_service_id takes precedence over machine_id.
        if parent_service_id:
            try:
                parent = query(Service).get(parent_service_id)
                # No, you should be able to specify the machine, and not take
                # the parent's machine, since services can be inherited and
                # be on different machines (obvious example: ssh -> ssh, most
                # probably on two different machines)
                #machine_id = parent.machine_id
            except:
                return vaultMsg(False, "No such parent service ID.",
                                {'parent_service_id': parent_service_id})

        # Get all users from the group_id, and all admins.
        encusers = list(query(Group).get(group_id).users)
        admusers = query(User).filter_by(is_admin=True).all()
        myselfuser = query(User).get(self.sess['user_id'])


        # Add service effectively..
        ns = Service()
        ns.machine_id = int(machine_id)
        ns.parent_service_id = parent_service_id or None
        ns.url = url
        ns.group_id = int(group_id)
        # seckey is the AES256 symmetric key, to be encrypted for each user.
        (seckey, ciphertext) = encrypt_secret(secret)
        ns.secret = ciphertext
        ns.secret_last_modified = datetime.now()
        ns.notes = notes

        meta.Session.save(ns)

        meta.Session.commit()


        # Add to users
        # Merge two lists (encusers, admusers)
        for adm in admusers:
            if adm not in encusers:
                encusers.append(adm)
        # Add myself
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
