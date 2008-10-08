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

"""SFLvaultAccess class file: main Vault access object.

This object is used over XML-RPC for remote requests, and used directly
for local access to the vault.

It is assumed here that full access is granted, or that security
filtering has been done at an earlier level (via an XML-RPC mechanism
for example).

This class only provides all the abstraction to the Vault, and should
return clean responses to clean queries.
"""


import xmlrpclib
from base64 import b64decode, b64encode
from datetime import *
import time as stdtime

from sqlalchemy import sql, exceptions

# from sflvault.lib:
from sflvault.model import *
from sflvault.lib.base import *

import logging
log = logging.getLogger('sflvault')

#
# Configuration
#
# TODO: make those configurable
SETUP_TIMEOUT = 300
SESSION_TIMEOUT = 300


class SFLvaultAccess(object):
    def __init__(self):
        """Init obj."""

        # This gives this object the knowledge of which user_id is currently
        # using the Vault
        self.myself_id = None

    
    def show(self, service_id):
        """Get the specified service ID and return the hierarchy to connect to it.

        We need self.myself_id to be set for this function.
        """
        try:
            s = query(Service).filter_by(id=service_id).one()
            #.options(model.eagerload('group'))
        except exceptions.InvalidRequestError, e:
            return vaultMsg(False, "Service not found: %s" % e.message)

        out = []
        while True:
            ucipher = query(Usercipher).filter_by(service_id=s.id, user_id=self.myself_id).first()
            if ucipher and ucipher.cryptsymkey:
                cipher = ucipher.cryptsymkey
            else:
                cipher = ''

            out.append({'id': s.id,
                        'url': s.url,
                        #'group': s.group.name or '',
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


    def search(self, search_query, verbose=False):
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

        
    def add_user(self, username, is_admin):

        usr = query(User).filter_by(username=username).first()

        msg = ''
        if usr == None:
            # New user
            usr = User()
            usr.waiting_setup =  datetime.now() + timedelta(0, SETUP_TIMEOUT)
            usr.username = username
            usr.is_admin = bool(is_admin)
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
                        ('Admin user' if is_admin else 'User',
                         msg, SETUP_TIMEOUT), {'user_id': usr.id})
        

    def grant(self, user, group_ids):
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
        srvs = []
        for g in groups:
            srvs.extend(g.services)

        # Unique-ify:
        srvs = list(set(srvs))

        # Grab mine and his Userciphers, we're going to fill in the gap
        hisid = usr.id
        myid = self.myself_id
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
  

    def grant_update(self, user, ciphers):
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


    def revoke(self, user, group_ids):
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


    def analyze(self, user):
        """Return a report of the left-overs (if any) of ciphers on a certain
        user. Report the number of missing ciphers, the amount to be removed,
        etc.."""

        # Get user, and relations
        try:
            # IMPORTANT: load this WITHOUT the 'userciphers.service' first
            # otherwise when we try to check the 'services' it will still
            # try to load the other relations, and it will conflict.
            usr = model.get_user(user)

        except LookupError, e:
            return vaultMsg(False, str(e))
        
        # All services user should have access to
        all_servs = usr.services

        # *now* only should we get those relations loaded:
        usr = model.get_user(user, 'userciphers.service')

        # Services for which user has already ciphers
        ciph_servs = [uc.service for uc in usr.userciphers \
                      if uc.service is not None]

        # Remove all userciphers that point to no service (uc.service == None)
        cleaned_ciphers = 0
        for uc in usr.userciphers:
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

        return vaultMsg(True, "Analysis report for user %s" % usr.username,
                        report)



    def add_machine(self, customer_id, name, fqdn, ip, location, notes):
        """Add a new machine to the database"""
        
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


    def add_service(self, machine_id, parent_service_id, url,
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

        for grp in groups:
            encusers.extend(grp.users)
        for adm in admusers:
            encusers.append(adm)

        
        if self.myself_id:
            myselfuser = query(User).get(self.myself_id)
            encusers.append(myselfuser)
        else:
            log.warning("You should *always* set myself_id on the " + \
                        self.__class__.__name__ + " object when calling "\
                        "add_service() to make sure the secret is "\
                        "encrypted for you at least.")

                
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
