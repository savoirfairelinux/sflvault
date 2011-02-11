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

from sqlalchemy import sql
from sqlalchemy.exceptions import InvalidRequestError as InvalidReq
from sqlalchemy.orm import eagerload_all

from sflvault.model import *
from sflvault.lib.base import *

import logging
log = logging.getLogger('sflvault')



class SFLvaultAccess(object):
    def __init__(self):
        """Init obj."""

        # This gives this object the knowledge of which user_id is currently
        # using the Vault
        self.myself_id = None
        # This gives this object the knowledge of which username is currently
        # using the Vault
        self.myself_username = None

        self.setup_timeout = 300

    def _log_any(self, log_func, msg, data):
        # Need to do that for user-setup
        if self.myself_username == None and self.myself_id == None:
            head = "NO USER - "
        else:
            head = "User: u#d%d - %s - " % (self.myself_id, self.myself_username)
        log_func(head + msg % data)

    def log_e(self, msg, data=None):
        self._log_any(log.error, msg, data)

    def log_i(self, msg, data=None):
        self._log_any(log.info, msg, data)

    def log_w(self, msg, data=None):
        self._log_any(log.warning, msg, data)


    def user_setup(self, username, pubkey):
        """Setup the user's account"""
        from pylons import app_globals

        u = query(User).filter_by(username=username).first()

        if u is None:
            self.log_i('No such temporary user %(username)s, add it first',
                       {"username": username})
            return vaultMsg(False, 'No such temporary user %s, add it first' % username)
        
        if u.setup_expired():
            self.log_i('Setup expired for user %(username)s',
                       {"username": username})
            return vaultMsg(False, 'Setup expired for user %s' % username)

        if u.pubkey:
            self.log_i('User %(username)s already has a publics',
                       {"username": username})
            return vaultMsg(False, 'User %s already has a public ' \
                                'key stored' % username)

        # Ok, let's save the things and reset waiting_setup.
        u.waiting_setup = None
        u.pubkey = pubkey
        
        # Save new informations
        meta.Session.add(u)
        meta.Session.commit()

        self.log_i('User setup complete for %(username)s',
                   {"username": username})
        return vaultMsg(True, 'User setup complete for %s' % username)


    def user_add(self, username, is_admin):
        usr = query(User).filter_by(username=username).first()

        msg = ''

        if usr is None:
            # New user
            usr = User()
            usr.waiting_setup =  datetime.now() + timedelta(0, int(self.setup_timeout))
            usr.username = username
            usr.is_admin = bool(is_admin)
            usr.created_time = datetime.now()

            meta.Session.add(usr)
            
            self.log_i('User %(username)s added.', {"username": username})
            msg = 'added'
        elif usr.waiting_setup:
            if usr.waiting_setup < datetime.now():
                # Verify if it's a waiting_setup user that has expired.
                usr.waiting_setup = datetime.now() + \
                                    timedelta(0, int(self.setup_timeout))
            
                self.log_i('updated (had setup timeout expired).', {})
                msg = 'updated (had setup timeout expired)'
            else:
                self.log_i('User %(username)s is waiting for setup.',
                       {"username": username})
                return vaultMsg(False, "User %s is waiting for setup" % \
                                username)
        else:
            self.log_i('User %(username)s already exists.',
                       {"username": username})
            return vaultMsg(False, 'User %s already exists.' % username)

        meta.Session.commit()

        return vaultMsg(True, '%s %s. User has a delay of %d seconds '
                              'to invoke a "user-setup" command' % \
                            ('Admin user' if is_admin else 'User',
                             msg, int(self.setup_timeout)), {'user_id': usr.id})
        

    def user_del(self, user):
        """Delete a user from database.

        :param user: can be a user_id, or username

        This will remove the user and it's links to groups.
        
        """
        try:
            usr = model.get_user(user)
        except LookupError, e:
            self.log_w('User UNsuccessfully deleted: %(error)s',
                        {'error': str(e)})
            return vaultMsg(False, str(e))

        t1 = model.usergroups_table
        meta.Session.execute(t1.delete(t1.c.user_id==usr.id))
        username = usr.username
        meta.Session.delete(usr)
        meta.Session.commit()
        self.log_i('User %(username)s successfully deleted.',
                   {"username": username})
        return vaultMsg(True, "User %s successfully deleted" % username)


    def user_list(self, groups=False):
        """Return a simple list of the users

        groups - return the list of groups for each user, or not
        """
        req = query(User)
        if groups:
            req = req.options(eagerload_all('groups_assoc.group'))
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

            if groups:
                # Loop group_assocs for that user..
                nx['groups'] = []
                for ug in x.groups_assoc:
                    nxgrp = {'is_admin': ug.is_admin,
                             'name': ug.group.name,
                             'id': ug.group_id}
                    nx['groups'].append(nxgrp)
                    
            out.append(nx)

        # Can use: datetime.fromtimestamp(x.created_stamp)
        # to get a datetime object back from the x.created_time
        return vaultMsg(True, "Here is the user list", {'list': out})
        

    def service_get(self, service_id, group_id=None):
        """Get a single service's data.

        group_id - return this group's key, otherwise, use first available
        """
        try:
            out = self._service_get_data(service_id, group_id)
        except VaultError, e:
            return vaultMsg(False, str(e))

        return vaultMsg(True, "Here is the service", {'service': out})
    

    def service_put(self, service_id, data):
        """Put a single service's data back to the vault's database"""

        try:
            s = query(Service).filter_by(id=service_id).one()
        except InvalidReq, e:
            self.log_i('Service not found: %(error)s', {"error": str(e)})
            return vaultMsg(False, "Service not found: %s" % str(e))

        #Save:
        # machine_id
        # parent_service_id
        # url
        # notes
        # location
        if 'machine_id' in data:
            s.machine_id = int(data['machine_id'])
        if 'parent_service_id' in data:
            if data['parent_service_id'] == '':
                s.parent_service_id = None
            else:
                s.parent_service_id = int(data['parent_service_id'])
        if 'notes' in data:
            s.notes = data['notes']
        if 'url' in data:
            s.url = data['url']
        if 'metadata' in data:
            s.metadata = data['metadata']

        meta.Session.commit()

        self.log_i('Service s#(service_id)s saved successfully' ,
                   {"service_id": service_id})
        return vaultMsg(True, "Service s#%s saved successfully" % service_id)

    def _service_get_data(self, service_id, group_id=None, with_groups=False):
        """Retrieve the information for a given service."""
        try:
            s = query(Service).filter_by(id=service_id).one()
        except InvalidReq, e:
            self.log_w('Service not found: %(service_id)s (%(error)s)',
                       {"service_id": service_id, "error": str(e)})
            raise VaultError("Service not found: %s (%s)" % (service_id,
                                                             str(e)))
        # unused
        #me = query(User).get(self.myself_id)

        # We need no aliasing, because we'll only use `cryptgroupkey`,
        # `cryptsymkey` and `group_id` in there.
        req = sql.join(servicegroups_table, usergroups_table,
                       ServiceGroup.group_id==UserGroup.group_id) \
                 .join(users_table, User.id==UserGroup.user_id) \
                 .select(use_labels=True) \
                 .where(User.id==self.myself_id) \
                 .where(ServiceGroup.service_id==s.id) \
                 .order_by(ServiceGroup.group_id)

        # Deal with group if specified..
        if group_id:
            req = req.where(ServiceGroup.group_id == group_id)
        
        res = meta.Session.execute(req)

        # Take the first one
        uciphers = list(res)
        if not uciphers:
            ugcgk = ''
            sgcsk = ''
            uggi = ''
        else:
            ucipher = uciphers[0]
            # WARN: these are table-name dependent!!
            ugcgk = ucipher.users_groups_cryptgroupkey
            sgcsk = ucipher.services_groups_cryptsymkey
            uggi = ucipher.users_groups_group_id

        groups_list = None
        # Load groups too if required
        if with_groups:
            groups_list = []
            req2 = sql.join(groups_table, servicegroups_table).select(use_labels=True).where(ServiceGroup.service_id == service_id)
            res2 = meta.Session.execute(req2)
            for grp in res2:
                groups_list.append((grp.groups_id, grp.groups_name))

        out = {'id': s.id,
               'url': s.url,
               'secret': s.secret,
               'machine_id': s.machine_id,
               'cryptgroupkey': ugcgk,
               'cryptsymkey': sgcsk,
               'group_id': uggi,
               'groups_list': groups_list,
               'parent_service_id': s.parent_service_id,
               'secret_last_modified': s.secret_last_modified,
               'metadata': s.metadata or {},
               'notes': s.notes or ''}

        return out

    def service_get_tree(self, service_id, with_groups=False):
        """Get a service tree, starting with service_id"""
        
        out = []
        while True:
            try:
                data = self._service_get_data(service_id,
                                              with_groups=with_groups)
            except VaultError, e:
                self.log_e('Show service: %(error)s', {"error": str(e)})
                return vaultMsg(False, str(e))
            
            out.append(data)

            if not data['parent_service_id']:
                break

            # Load the parent...
            service_id = data['parent_service_id']

            # check if we're not in an infinite loop!
            if service_id in [x['id'] for x in out]:
                self.log_e('Circular references of parent services, aborting.', {})
                return vaultMsg(False, "Circular references of parent services, aborting.")

        out.reverse()


        self.log_i('Service shown: %(service_id)s', {"service_id": service_id})
        return vaultMsg(True, "Here are the services", {'services': out})    

    
    def show(self, service_id, with_groups=False):
        """Get the specified service ID and return the hierarchy to connect
        to it or to show it.

        We need self.myself_id to be set for this function.
        """
        return self.service_get_tree(service_id, with_groups)


    def search(self, search_query, filters=None, verbose=False):
        """Do the search, and return the result tree.

        filters - must be a dictionary with options on which to constraint
                  results.

        """
        filter_types = ['groups', 'machines', 'customers']
        # Load objects on which to restrict the query:
        newfilters = {}
        if filters:
            if not isinstance(filters, dict):
                self.log_e('Search: filters must be a dictionary')
                return vaultMsg(False, "filters must be a dictionary")
            for flt in filter_types:
                # Skip filters that aren't specified
                if flt not in filters:
                    continue

                # Skip filters that are empty or None
                if not filters[flt]:
                    continue

                try:
                    newfilters[flt] = model.get_objects_ids(filters[flt], flt)
                except ValueError, e:
                    self.log_e('Search error: %(error)s' % {"error": str(e)})
                    return vaultMsg(False, str(e))

        search = model.search_query(search_query, newfilters, verbose)


        # Quick helper funcs, to create the hierarchical 'out' structure.
        def set_customer(out, c):
            "Subfunc of search"
            if out.has_key(str(c.customers_id)):
                return
            out[str(c.customers_id)] = {'name': c.customers_name,
                                        'machines': {}}
            
        def set_machine(subout, m):
            "Subfunc of search"
            if subout.has_key(str(m.machines_id)):
                return
            subout[str(m.machines_id)] = {'name': m.machines_name,
                            'fqdn': m.machines_fqdn or '',
                            'ip': m.machines_ip or '',
                            'location': m.machines_location or '',
                            'notes': m.machines_notes or '',
                            'services': {}}
            
        def set_service(subsubout, s):
            "Subfunc of search"
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
        #self.log_i('Search successfull for: %(search)s',
        #            {'search': search_query})
        return vaultMsg(True, "Here are the search results", {'results': out})


    def customer_get(self, customer_id):
        """Get a single customer's data"""
        try:
            cust = query(Customer).filter_by(id=customer_id).one()
        except InvalidReq, e:
            self.log_i('Customer not found: %(error)s', {"error": str(e)})
            return vaultMsg(False, "Customer not found: %s" % str(e))

        out = {'id': cust.id,
               'name': cust.name}

        return vaultMsg(True, "Here is the customer", {'customer': out})

    def customer_put(self, customer_id, data):
        """Put a single customer's data back to the Vault"""
        try:
            cust = query(Customer).filter_by(id=customer_id).one()
        except InvalidReq, e:
            self.log_w('Customer not found: %(customer_id)s',
                       {"customer_id": customer_id})
            return vaultMsg(False, "Customer not found: %s" % str(e))

        if 'name' in data:
            cust.name = data['name']

        meta.Session.commit()

        self.log_i('Customer c#%(customer_id)s saved successfully)s',
                  {"customer_id": customer_id})
        return vaultMsg(True, "Customer c#%s saved successfully" % customer_id)


    def customer_add(self, customer_name):
        """Add a new customer to the database"""
        nc = Customer()
        nc.name = customer_name
        nc.created_time = datetime.now()
        nc.created_user = self.myself_username
        if not self.myself_username:
            log.warning("You should *always* set myself_username on the " + \
                        self.__class__.__name__ + " object when calling "\
                        "add_customer() to log creation time and user infos.")

        meta.Session.save(nc)
        
        meta.Session.commit()

        self.log_i('Customer add: c#%(customer_id)s', {"customer_id": nc.id})
        return vaultMsg(True, 'Customer added', {'customer_id': nc.id})


    def machine_put(self, machine_id, data):
        """Put a single machine's data back to the vault"""
        try:
            m = query(Machine).filter_by(id=machine_id).one()
        except InvalidReq, e:
            self.log_w('Machine m#%(machine_id)s saved successfully',
                   {"machine_id": machine_id})
            return vaultMsg(False, "Machine not found: %s" % str(e))

        if 'customer_id' in data:
            m.customer_id = int(data['customer_id'])

        for x in ['ip', 'name', 'fqdn', 'location', 'notes']:
            if x in data:
                m.__setattr__(x, data[x])
        meta.Session.commit()

        self.log_i('Machine m#%(machine_id)s saved successfully',
                   {"machine_id": machine_id})
        return vaultMsg(True, "Machine m#%s saved successfully" % machine_id)

    def machine_get(self, machine_id):
        """Get a single machine's data"""
        try:
            m = query(Machine).filter_by(id=machine_id).one()
        except InvalidReq, e:
            return vaultMsg(False, "Machine not found: %s" % str(e))


        out = {'id': m.id,
               'ip': m.ip or '',
               'fqdn': m.fqdn or '',
               'name': m.name or '',
               'location': m.location or '',
               'notes': m.notes or '',
               'customer_id': m.customer_id}

        return vaultMsg(True, "Here is the machine", {'machine': out})  


    def machine_add(self, customer_id, name, fqdn, ip, location, notes):
        """Add a new machine to the database"""
        
        nm = Machine()
        nm.customer_id = int(customer_id)
        nm.created_time = datetime.now()
        if not name:
            return vaultMsg(False, "Missing required argument: name")
        nm.name = name
        nm.fqdn = fqdn or ''
        nm.ip = ip or ''
        nm.location = location or ''
        nm.notes = notes or ''

        meta.Session.save(nm)
        
        meta.Session.commit()

        self.log_i('Machine added: m#%(machine_id)s', {"machine_id": nm.id})
        return vaultMsg(True, "Machine added.", {'machine_id': nm.id})


    def service_add(self, machine_id, parent_service_id, url,
                    group_ids, secret, notes, metadata):
        # Get groups
        try:
            groups, group_ids = model.get_objects_list(group_ids, 'groups',
                                                       return_objects=True)
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

        # seckey is the AES256 symmetric key, to be encrypted for each user.
        (seckey, ciphertext) = encrypt_secret(secret)

        # Add service effectively..
        ns = Service()
        ns.machine_id = int(machine_id)
        ns.parent_service_id = parent_service_id or None
        ns.url = url
        ns.secret = ciphertext
        ns.secret_last_modified = datetime.now()
        ns.notes = notes
        ns.metadata = metadata

        meta.Session.save(ns)

        # Encrypt symkey for each group, using it's own ElGamal pubkey
        for g in groups:
            eg = g.elgamal()
            
            nsg = ServiceGroup()
            nsg.group_id = g.id
            nsg.cryptsymkey = encrypt_longmsg(eg, seckey)
            
            ns.groups_assoc.append(nsg)

        del(seckey)

        meta.Session.commit()

        grouplist = [g.name for g in groups]

        return vaultMsg(True, "Service added.", {'service_id': ns.id,
                                                 'encrypted_for': grouplist})

    def group_get(self, group_id):
        """Get a single group's data"""
        try:
            grp = query(Group).filter_by(id=group_id).one()
        except InvalidReq, e:
            return vaultMsg(False, "Group not found: %s" % str(e))

        ug = query(UserGroup).filter_by(user_id=self.myself_id,
                                        group_id=group_id).first()

        # TODO: don't allow if grp.hidden == True and user isn't part of the
        # group.

        out = {'id': grp.id,
               'name': grp.name,
               'hidden': grp.hidden}

        if grp.hidden and (not ug or not ug.is_admin):
            return vaultMsg(False, "Group not found*")

        if ug:
            out['cryptgroupkey'] = ug.cryptgroupkey
        
        return vaultMsg(True, "Here is the group", {'group': out})


    def group_put(self, group_id, data):
        """Put a single group's data back to the Vault"""
        try:
            grp = query(Group).filter_by(id=group_id).one()
        except InvalidReq, e:
            return vaultMsg(False, "Group not found: %s" % str(e))

        ug = query(UserGroup).filter_by(user_id=self.myself_id,
                                        group_id=group_id).first()
        if not ug:
            return vaultMsg(False, "Cannot write to group: not member of group")

        if 'name' in data:
            grp.name = data['name']
            
        if 'hidden' in data:
            newhidden = bool(data['hidden'])
            # TODO: these checks must go in the XML-RPC controller.
            if not ug.is_admin and newhidden:
                return vaultMsg(False, "You need to be admin on this group "
                                "to hide the group")
            grp.hidden = newhidden

        meta.Session.commit()

        return vaultMsg(True, "Group g#%s saved successfully" % group_id)


    def group_add(self, group_name, hidden=False):
        """Add a new group the database. Nothing will be added to it
        by default"""

        # Get my User, to get my pubkey.
        me = query(User).get(self.myself_id)
        myeg = me.elgamal()
        
        # Generate keypair
        newkeys = generate_elgamal_keypair()
        
        ng = Group()
        ng.name = group_name
        ng.hidden = hidden
        ng.pubkey = serial_elgamal_pubkey(elgamal_pubkey(newkeys))

        meta.Session.save(ng)

        meta.Session.commit()

        # Add myself to the group and all other global admins.
        admins = set(query(User).filter_by(is_admin=True).all())
        admins.add(me)

        for usr in list(admins):
            nug = UserGroup()
            # Make sure I'm admin of my newly created group
            if usr == me:
                nug.is_admin = True
            nug.user_id = usr.id
            nug.cryptgroupkey = encrypt_longmsg(usr.elgamal(),
                                                serial_elgamal_privkey(
                                                    elgamal_bothkeys(newkeys)))
            ng.users_assoc.append(nug)
        
        meta.Session.commit()

        return vaultMsg(True, "Added group '%s'" % ng.name,
                        {'name': ng.name, 'group_id': int(ng.id),
                         'cryptgroupkey': nug.cryptgroupkey})

    def group_del(self, group_id):
        """Remove a group from the vault. Only if no services are associated
        with it anymore."""        
        grp = query(Group).options(eagerload('services_assoc')).filter_by(id=int(group_id)).first()

        if grp is None:
            return vaultMsg(False, "Group not found: %s" % (group_id,))
        
        if len(grp.services_assoc):
            return vaultMsg(False, "Group not empty, cannot delete")

        # Delete UserGroup elements...
        q1 = usergroups_table.delete(UserGroup.group_id==grp.id)
        meta.Session.execute(q1)

        name = grp.name
        # Delete Group and commit..
        meta.Session.delete(grp)
        meta.Session.commit()

        retval = {'name': name,
                  'group_id': group_id}
        return vaultMsg(True, 'Removed group "%s" successfully' % name, retval)


    def group_list(self, show_hidden=False, list_users=False):
        """Return a simple list of the available groups"""
        groups = query(Group).options(eagerload_all('users_assoc.user')).all()

        me = query(User).get(self.myself_id)

        out = []
        for grp in groups:
            myug = [ug for ug in grp.users_assoc if ug.user_id == me.id]
            
            res = {'id': grp.id,
                   'name': grp.name,
                   'member': me in grp.users,
                   'hidden': False,
                   'admin': False}

            if grp.hidden:
                # Only for global-admin or members, if we're asked to hide
                # hidden groups
                if not show_hidden and not me.is_admin and not myug:
                    continue
                res['hidden'] = True

            if len(myug):
                res['cryptgroupkey'] = myug[0].cryptgroupkey
                if myug[0].is_admin:
                    res['admin'] = True
            
            print "A" * 1000
            print grp.users_assoc
            print grp.users
            res['members'] = [(u.user_id, u.user.username, u.is_admin)
                              for u in grp.users_assoc]

            out.append(res)

        return vaultMsg(True, 'Here is the list of groups', {'list': out})


    def group_add_service(self, group_id, service_id, symkey):
        """Add a service to a group.

        Call servie_get() first to get the information and decrypt the symkey
        on your side, then call this function to store the symkey.

        The server-side Vault will encrypt it for the given group.
        """

        try:
            grp = query(Group).filter_by(id=group_id).one()
        except InvalidReq, e:
            return vaultMsg(False, "Group not found: %s" % str(e))

        grpeg = grp.elgamal()

        sg = query(ServiceGroup).filter_by(group_id=group_id,
                                           service_id=service_id).all()
        if len(sg):
            return vaultMsg(False, "Service is already in group")

        # Store the data in the vault.
        nsg = ServiceGroup()
        nsg.group_id = group_id
        nsg.service_id = service_id
        nsg.cryptsymkey = encrypt_longmsg(grpeg, symkey)

        meta.Session.save(nsg)
        meta.Session.commit()
        
        return vaultMsg(True, "Added service to group successfully", {})


    def group_del_service(self, group_id, service_id):
        """Remove the association between a group and a service, simply."""
        grp = query(Group).filter_by(id=group_id).first()

        if not grp:
            return vaultMsg(False, "Group not found: %s" % str(e))

        # TODO: DRY out this place, much copy from del_user and stuff
        sgs = query(ServiceGroup).filter_by(service_id=service_id).all()

        if grp.id not in [sg.group_id for sg in sgs]:
            return vaultMsg(False, "Service is not in group: %s" % str(e))

        sg = [sg for sg in sgs if grp.id == sg.group_id][0]
            
        # Make sure we don't lose all of the service's crypted information.
        if len(sgs) < 2:
            return vaultMsg(False, "This is the last group this service is in. Either delete the service, or add it to another group first")

        # Remove the GroupService from the Group object.
        meta.Session.delete(sg)
        meta.Session.commit()

        return vaultMsg(True, "Removed service from group successfully")


    def group_add_user(self, group_id, user, is_admin=False,
                       cryptgroupkey=None):
        """Add a user to a group. Call once to retrieve information,
        and a second time with cryptgroupkey to save cipher information.

        The second call should give the group's privkey, encrypted by the
        remote user for the user being added.

        is_admin - Gives admin privileges to the user being added or not.
        user - User can be a username or a user_id
        """
        try:
            grp = query(Group).filter_by(id=group_id).one()
        except InvalidReq, e:
            return vaultMsg(False, "Group not found: %s" % str(e))

        # Verify if I'm admin on that group
        ug = query(UserGroup).filter_by(group_id=group_id,
                                        user_id=self.myself_id).first()

        # Make sure I'm in that group (to be able to decrypt the groupkey)
        if not ug:
            return vaultMsg(False, "You are not part of that group")

        # No admin checks, you NEED to be in the group to return consistantly
        # encrypted cryptgroupkey

        # Find added user
        try:
            usr = get_user(user)
        except LookupError, e:
            return vaultMsg(False, "User %s not found: %s" % (user, str(e)))


        # Make sure we don't double the group access.
        if query(UserGroup).filter_by(group_id=group_id,
                                  user_id=usr.id).first():
            return vaultMsg(False, "User %s is already in that group" % user)
        
        if not cryptgroupkey:
            # Return the required information for a second call to work.
            ret = {'user_id': int(usr.id),
                   'group_id': int(group_id),
                   'userpubkey': usr.pubkey,
                   'cryptgroupkey': ug.cryptgroupkey}
            return vaultMsg(True, "Continue, send the cryptgroupkey back, encrypted by the userpubkey provided", ret)
        
        nug = UserGroup()
        nug.user_id = usr.id
        nug.group_id = group_id
        nug.is_admin = is_admin
        # NOTE: This command trusts that the remote user adding another user
        # enters valid data as a cryptgroupkey. If junk is added in that field,
        # the added user simply won't be able to access the group's data.
        # Also will he need to be removed and added successfully to the group
        # for everything to work.
        nug.cryptgroupkey = cryptgroupkey

        meta.Session.save(nug)
        meta.Session.commit()
        
        return vaultMsg(True, "Added user to group successfully")


    def group_del_user(self, group_id, user):
        """Remove the association between a group and a user.

        Make sure there are still 'is_admin' users associated with the group
        to be able to give access to someone else in case of need.

        SFLvault will refuse to delete a user from a group if no other users
        are part of that group, and if the group still has some services
        associated with it. First, call group_del_service from the group for
        all services, then delete the users, and then the group.

        user - can be a username or a user_id
        """
        # TODO: DRY out this place, much copy from group_add_user
        try:
            grp = query(Group).filter_by(id=group_id).one()
        except InvalidReq, e:
            return vaultMsg(False, "Group not found: %s" % str(e))

        # Verify if I'm admin on that group
        ugs = query(UserGroup).filter_by(group_id=group_id).all()

        myug = [ug for ug in ugs if ug.user_id == self.myself_id]
        if not myug:
            return vaultMsg(False, "You are not part of that group")

        ug = myug[0] # This is my UserGroup row.
        
        me = query(User).get(self.myself_id)
        
        if not ug.is_admin and not me.is_admin:
            return vaultMsg(False, "You are not admin on that group (nor global admin)")

        # Find added user
        try:
            usr = get_user(user)
        except LookupError, e:
            return vaultMsg(False, "User %s not found: %s" % (user, str(e)))

        hisug = [ug for ug in ugs if ug.user_id == usr.id]

        if not hisug:
            return vaultMsg(False, "User isn't part of the group")

        # Check I'm not removing myself
        if self.myself_id == usr.id:
            return vaultMsg(False, "Cannot remove yourself from a group")

        # This also prevents from removing myself from the group.
        if len(ugs) < 2:
            return vaultMsg(False, "Only one user left! Cannot leave a group unattended, otherwise all service will become lost!")

        # If we're using the library, we must make sure there is still a
        # group admin left.  This simplifiest the rescues :)
        id_admins = [x.id for x in ugs if x.is_admin]
        if id_admins == [usr.id]:
            return vaultMsg(False, "Each group must have at least one group-admin.  You cannot delete the last group-admin.")
        
        ohoh = ''
        if not id_admins:
            ohoh = " - WARNING: there are no more group-admins in this group.  Ask a global-admin to elect someone group-admin for further management of this group."

        meta.Session.delete(hisug[0])
        meta.Session.commit()

        return vaultMsg(True, "Removed user from group successfully" + ohoh, {})
        

    def customer_del(self, customer_id):
        """Delete a customer from database, bringing along all it's machines
        and services
        """
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

        # Delete all related groupciphers
        d = sql.delete(model.servicegroups_table) \
               .where(model.servicegroups_table.c.service_id.in_(servs_ids))
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


    def machine_del(self, machine_id):
        """Delete a machine from database, bringing on all child services."""
        
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


        # Delete all related groupciphers
        d = sql.delete(model.servicegroups_table) \
               .where(model.servicegroups_table.c.service_id.in_(servs_ids))
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


    def service_del(self, service_id):
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

        # TODO: verify permissions:
        #  if either user is global admin, or is admin of all groups in which this
        #  service is in, otherwise, disallow.
        
        # Delete all related user-ciphers
        d = sql.delete(model.servicegroups_table) \
               .where(model.servicegroups_table.c.service_id == service_id)
        # Delete the service
        d2 = sql.delete(services_table) \
                .where(services_table.c.id == service_id)
        
        meta.Session.execute(d)
        meta.Session.execute(d2)
        meta.Session.commit()

        return vaultMsg(True, 'Deleted service s#%s successfully' % service_id)



    def customer_list(self):
        lst = query(Customer).all()

        out = []
        for x in lst:
            nx = {'id': x.id, 'name': x.name}
            out.append(nx)

        return vaultMsg(True, 'Here is the customer list', {'list': out})



    def machine_list(self, customer_id=None):
        """Return a simple list of the machines"""    
        sel = sql.join(customers_table, machines_table) \
                 .select(use_labels=True) \
                 .order_by(Customer.id)

        # Filter also..
        if customer_id:
            sel = sel.where(Customer.id==customer_id)
        
        lst = meta.Session.execute(sel)

        out = [{'id': x.machines_id, 'name': x.machines_name,
                  'fqdn': x.machines_fqdn, 'ip': x.machines_ip,
                  'location': x.machines_location, 'notes': x.machines_notes,
                  'customer_id': x.customers_id,
                  'customer_name': x.customers_name}
               for x in lst]

        return vaultMsg(True, "Here is the machines list", {'list': out})
    

    def service_list(self, machine_id=None, customer_id=None):
        """Return a simple list of the services"""
        services = query(Service).join('machine')

        # Filter also..
        if machine_id:
            services = services.filter(Service.machine_id==int(machine_id))
        if customer_id:
            services = services.filter(Machine.customer_id==int(customer_id))

        out = [{'id': s.id, 'url': s.url,
                   'parent_service_id': s.parent_service_id,
                   'metadata': s.metadata, 'notes': s.notes,
                   'machine_id': s.machine_id,
                   'secret': s.secret,
                   'secret_last_modified': s.secret_last_modified,
                }
               for s in services]

        return vaultMsg(True, "Here is the machines list", {'list': out})


    def service_passwd(self, service_id, newsecret):
        """Change the passwd for a given service"""
        # number please
        service_id = int(service_id)

        serv = query(Service).get(service_id)
        groups = serv.groups

        (seckey, ciphertext) = encrypt_secret(newsecret)
        serv.secret = ciphertext
        
        # TODO absolutely:  verify this requesting user has access to the
        # password first.  YES, he can add a new password, but not modify
        # something he doesn't have access to, first.

        for sg in serv.groups_assoc:
            eg = [g for g in groups if g.id == sg.group_id][0].elgamal()
            sg.cryptsymkey = encrypt_longmsg(eg, seckey)

        meta.Session.commit()

        grouplist = [g.name for g in groups]
        
        return vaultMsg(True, "Service added.", {'service_id': service_id,
                                                 'encrypted_for': grouplist})
