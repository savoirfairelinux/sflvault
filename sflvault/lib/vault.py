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


    def service_get(self, service_id):
        """Get a single service's data"""
        try:
            s = query(Service).filter_by(id=service_id).one()
        except exceptions.InvalidRequestError, e:
            return vaultMsg(False, "Service not found: %s" % e.message)

        ucipher = query(Usercipher).filter_by(service_id=s.id, user_id=self.myself_id).first()
        if ucipher and ucipher.cryptsymkey:
            cipher = ucipher.cryptsymkey
        else:
            cipher = ''

        out = {'id': s.id,
               'machine_id': s.machine_id or '',
               'parent_service_id': s.parent_service_id or '',
               'url': s.url or '',
               'secret': s.secret,
               'usercipher': cipher,
               'secret_last_modified': s.secret_last_modified,
               'metadata': s.metadata or '',
               'notes': s.notes or ''}

        return vaultMsg(True, "Here is the service", {'service': out})
    

    def service_put(self, service_id, data):
        """Put a single service's data back to the vault's database"""

        try:
            s = query(Service).filter_by(id=service_id).one()
        except exceptions.InvalidRequestError, e:
            return vaultMsg(False, "Service not found: %s" % e.message)

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

        meta.Session.commit()

        return vaultMsg(True, "Service s#%s saved successfully" % service_id)

    def service_get_tree(self, service_id):
        """Get a service tree, starting with service_id"""
        
        try:
            s = query(Service).filter_by(id=service_id).one()
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

    
    def show(self, service_id):
        """Get the specified service ID and return the hierarchy to connect
        to it or to show it.

        We need self.myself_id to be set for this function.
        """
        return self.service_get_tree(service_id)


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


    def user_add(self, username, is_admin):

        usr = query(User).filter_by(username=username).first()

        msg = ''
        if usr == None:
            # New user
            usr = User()
            usr.waiting_setup =  datetime.now() + timedelta(0, int(self.setup_timeout))
            usr.username = username
            usr.is_admin = bool(is_admin)
            usr.created_time = datetime.now()

            meta.Session.save(usr)
            
            msg = 'added'
        elif usr.waiting_setup:
            if usr.waiting_setup < datetime.now():
                # Verify if it's a waiting_setup user that has expired.
                usr.waiting_setup = datetime.now() + \
                                    timedelta(0, int(self.setup_timeout))
            
                msg = 'updated (had setup timeout expired)'
            else:
                return vaultMsg(False, "User %s is waiting for setup" % \
                                username)
        else:
            return vaultMsg(False, 'User %s already exists.' % username)
        
        meta.Session.commit()

        return vaultMsg(True, '%s %s. User has a delay of %d seconds to invoke a "user-setup" command' % \
                        ('Admin user' if is_admin else 'User',
                         msg, int(self.setup_timeout)), {'user_id': usr.id})
        


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

        return vaultMsg(True, 'Customer added', {'customer_id': nc.id})


    def machine_put(self, machine_id, data):
        """Put a single machine's data back to the vault"""
        try:
            m = query(Machine).filter_by(id=machine_id).one()
        except exceptions.InvalidRequestError, e:
            return vaultMsg(False, "Machine not found: %s" % e.message)

        if 'customer_id' in data:
            m.customer_id = int(data['customer_id'])

        for x in ['ip', 'name', 'fqdn', 'location', 'notes']:
            if x in data:
                m.__setattr__(x, data[x])
        
        #         if 'ip' in data:
        #             m.ip = data['ip']
        #         if 'name' in data:
        #             m.name = data['name']
        #         if 'fqdn' in data:
        #             m.fqdn = data['fqdn']
        #         if 'location' in data:
        #             m.location = data['location']
        #         if 'notes' in data:
        #             m.notes = data['notes']

        meta.Session.commit()

        return vaultMsg(True, "Machine m#%s saved successfully" % machine_id)

    def machine_get(self, machine_id):
        """Get a single machine's data"""
        try:
            m = query(Machine).filter_by(id=machine_id).one()
        except exceptions.InvalidRequestError, e:
            return vaultMsg(False, "Machine not found: %s" % e.message)


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
            return vaultMsg(False, "Missing requierd argument: name")
        nm.name = name
        nm.fqdn = fqdn or ''
        nm.ip = ip or ''
        nm.location = location or ''
        nm.notes = notes or ''

        meta.Session.save(nm)
        
        meta.Session.commit()

        return vaultMsg(True, "Machine added.", {'machine_id': nm.id})


    def service_add(self, machine_id, parent_service_id, url,
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


        userlist = self._encrypt_service_seckey(ns.id, seckey, groups)

        return vaultMsg(True, "Service added.", {'service_id': ns.id,
                                                 'encrypted_for': userlist})


    def user_del(self, user):
        """Delete a user from database"""
        # Get user
        try:
            usr = model.get_user(user)
        except LookupError, e:
            return vaultMsg(False, str(e))

        t1 = model.usergroups_table
        t2 = model.userciphers_table
        meta.Session.execute(t1.delete(t1.c.user_id==usr.id))
        meta.Session.execute(t2.delete(t2.c.user_id==usr.id))
        
        meta.Session.delete(usr)
        meta.Session.commit()

        return vaultMsg(True, "User successfully deleted")


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



    def customer_list(self):
        lst = query(Customer).all()

        out = []
        for x in lst:
            nx = {'id': x.id, 'name': x.name}
            out.append(nx)

        return vaultMsg(True, 'Here is the customer list', {'list': out})


    def group_add(self, group_name):
        """Add a new group the database. Nothing will be added to it
        by default"""
        
        ng = Group()
        ng.name = group_name

        meta.Session.save(ng)
        meta.Session.commit()

        return vaultMsg(True, "Added group '%s'" % ng.name,
                        {'name': ng.name, 'group_id': int(ng.id)})

    def group_list(self):
        """Return a simple list of the available groups"""
        # TODO: implement hidden groups, you shouldn't show those groups,
        #       unless you're admin of that group.
        groups = query(Group).group_by(Group.name).all()

        out = []
        for x in groups:
            out.append({'id': x.id, 'name': x.name})

        return vaultMsg(True, 'Here is the list of groups', {'list': out})


    def machine_list(self, customer_id=None):
        """Return a simple list of the machines"""
        
        sel = sql.join(Machine, Customer) \
                 .select(use_labels=True) \
                 .order_by(Customer.id)

        # Filter also..
        if customer_id:
            sel = sel.where(Customer.id==customer_id)
        
        lst = meta.Session.execute(sel)

        out = []
        for x in lst:
            nx = {'id': x.machines_id, 'name': x.machines_name,
                  'fqdn': x.machines_fqdn, 'ip': x.machines_ip,
                  'location': x.machines_location, 'notes': x.machines_notes,
                  'customer_id': x.customers_id,
                  'customer_name': x.customers_name}
            out.append(nx)

        return vaultMsg(True, "Here is the machines list", {'list': out})
    

    def user_list(self):
        """Return a simple list of the users"""
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


    def _encrypt_service_seckey(self, service_id, seckey, groups):
        """Encrypt secret for a given service with the public key of
        everyone who has access to it."""
        # Get all users from the group_ids, and all admins and the requestor.
        encusers = []
        admusers = query(User).filter_by(is_admin=True).all()

        for grp in groups:
            encusers.extend(grp.users)
        for adm in admusers:
            encusers.append(adm)

        # Add myself to the list
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
            nu.service_id = service_id
            nu.user_id = usr.id

            eg = usr.elgamal()
            nu.cryptsymkey = serial_elgamal_msg(eg.encrypt(seckey,
                                                           randfunc(32)))
            del(eg)

            meta.Session.save(nu)
            
            userlist.append(usr.username) # To return listing.

        meta.Session.commit()

        del(seckey)

        return userlist
        

    def service_passwd(self, service_id, newsecret):
        """Change the passwd for a given service"""
        # number please
        service_id = int(service_id)

        serv = query(Service).get(service_id)
        groups = serv.groups

        (seckey, ciphertext) = encrypt_secret(newsecret)
        serv.secret = ciphertext
        
        # Effacer tous les Ciphers pour ce service avant.
        # TODO: we must check out that we don't delete VERSIONED ciphers
        #       when we add versioning to the userciphers_table.
        t1 = model.userciphers_table
        meta.Session.execute(t1.delete(t1.c.service_id == service_id))

        meta.Session.commit()

        userlist = self._encrypt_service_seckey(service_id, seckey, groups)
        
        return vaultMsg(True, "Service added.", {'service_id': service_id,
                                                 'encrypted_for': userlist})
