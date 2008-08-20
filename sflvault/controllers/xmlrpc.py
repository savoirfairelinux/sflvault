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

log = logging.getLogger(__name__)

#
# Configuration
#
# TODO: make those configurable
SETUP_TIMEOUT = 60
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
            u = User.query().filter_by(username=username).one()
        except:
            return vaultMsg(True, 'User unknown')
        # TODO: implement throttling ?

        rnd = randfunc(32)
        # 15 seconds to complete login/authenticate round-trip.
        u.logging_timeout = datetime.now() + timedelta(0, 15)
        u.logging_token = b64encode(rnd)

        Session.flush()
        Session.commit()

        e = u.elgamal()
        cryptok = serial_elgamal_msg(e.encrypt(rnd, randfunc(32)))
        return vaultMsg(False, 'Authenticate please', {'cryptok': cryptok})

    def sflvault_authenticate(self, username, cryptok):
        """Receive the *decrypted* cryptok, b64 encoded"""

        u = None
        try:
            u = User.query.options(lazyload('levels')).filter_by(username=username).one()
        except:
            return vaultMsg(True, 'Invalid user')

        if u.logging_timeout < datetime.now():
            return vaultMsg(True, 'Login token expired. Now: %s Timeout: %s' % (datetime.now(), u.logging_timeout))

        # str() necessary, to convert buffer to string.
        if cryptok != str(u.logging_token):
            return vaultMsg(True, 'Authentication failed')
        else:
            newtok = b64encode(randfunc(32))
            set_session(newtok, {'username': username,
                                 'timeout': datetime.now() + timedelta(0, SESSION_TIMEOUT),
                                 'userobj': u
                                 })

            return vaultMsg(False, 'Authentication successful', {'authtok': newtok})



    def sflvault_setup(self, username, pubkey):

        # First, remove ALL users that have waiting_setup expired, where
        # waiting_setup isn't NULL.
        #Session.delete(User.query().filter(User.waiting_setup != None).filter(User.waiting_setup < datetime.now()))
        #raise RuntimeError
        cnt = User.query().count()
        
        u = User.query().filter_by(username=username).first()


        if (cnt):
            if (not u):
                return vaultMsg(True, 'No such user %s' % username)
        
            if (u.setup_expired()):
                return vaultMsg(True, 'Setup expired for user %s' % username)

        # Ok, let's save the things and reset waiting_setup.
        u.waiting_setup = None
        u.pubkey = pubkey

        Session.commit()

        return vaultMsg(False, 'User setup complete for %s' % username)


    @authenticated_user
    def sflvault_show(self, authtok, vid):
        """Get the specified service ID and return the hierarchy to connect to it."""
        try:
            s = Service.query.filter_by(id=vid).one()
        except:
            return vaultMsg(True, "Service not found")

        out = []
        while True:
            ucipher = Usercipher.query.filter_by(service_id=s.id, user_id=self.sess['userobj'].id).first()
            if ucipher and ucipher.stuff:
                cipher = ucipher.stuff
            else:
                cipher = ''

            out.append({'id': s.id,
                        'url': s.url,
                        'level': s.level or '',
                        'secret': s.secret,
                        'usercipher': cipher,
                        'secret_last_modified': s.secret_last_modified,
                        'metadata': s.metadata or '',
                        'notes': s.notes or ''})

            if not s.parent:
                break
            
            s = s.parent

            # check if we're not in an infinite loop!
            if s.id in [x['id'] for x in out]:
                return vaultMsg(True, "Circular references of parent services, aborting.")

        out.reverse()

        return vaultMsg(False, "Here are the services", {'services': out})


    @authenticated_user
    def sflvault_search(self, authtok, query):
        """Do the search, and return the result tree."""
        # TODO: narrow down search (instead of all(), doh!)
        cs = Customer.query.all()
        ms = Machine.query.all()
        ss = Service.query.all()

        # Quick helper funcs, to create the hierarchical 'out' structure.
        def set_customer(out, c):
            if out.has_key(str(c.id)):
                return
            out[str(c.id)] = {'name': c.name,
                         'machines': {}}
        def set_machine(subout, m):
            if subout.has_key(str(m.id)):
                return
            subout[str(m.id)] = {'name': m.name,
                            'fqdn': m.fqdn or '',
                            'ip': m.ip or '',
                            'location': m.location or '',
                            'notes': m.notes or '',
                            'services': {}}
        def set_service(subsubout, s):
            subsubout[str(s.id)] = {'url': s.url,
                               'level': s.level or '',
                               'parent_service_id': s.parent_service_id or '',
                               # DON'T INCLUDE secret, when we're just searching
                               #'secret': s.secret or '',
                               'metadata': s.metadata or '',
                               'notes': s.notes or ''}

        out = {}
        # Loop services, setup machines and customers first.
        for x in ss:
            # Setup customer dans le out, pour le service
            set_customer(out, x.machine.customer)
            set_machine(out[str(x.machine.customer.id)]['machines'], x.machine)
            set_service(out[str(x.machine.customer.id)]['machines'][str(x.machine.id)]['services'], x)

        # Loop machines, setup customers first.
        for y in ms:
            set_customer(out, y.customer)
            set_machine(out[str(y.customer.id)]['machines'], y)

        # Loop customers !
        for z in cs:
            set_customer(out, z)

        # Return 'out', in a nicely structured hierarchical form.
        return vaultMsg(False, "Here are the search results", {'results': out})
        

    @authenticated_admin
    def sflvault_adduser(self, authtok, username, admin):
        if (User.query().filter_by(username=username).count()):
            return vaultMsg(True, 'User %s already exists.' % username)
        
        n = User()
        n.waiting_setup =  datetime.now() + timedelta(0, SETUP_TIMEOUT)
        n.username = username
        n.is_admin = admin
        n.created_time = datetime.now()

        Session.commit()

        return vaultMsg(False, '%s added. User has a delay of %d seconds to invoke a "setup" command' % (admin and 'Admin user' or 'User',
                                                                                                         SETUP_TIMEOUT), {'user_id': n.id})


    @authenticated_admin
    def sflvault_grant(self, authtok, user, levels):
        """Can get user as user_id, or username"""
        # Add UserLevels corresponding to each levels in the dict
        if isinstance(user, int):
            usr = User.query().filter_by(id=user).first()
        else:
            usr = User.query().filter_by(username=user).first()

        if not usr:
            return vaultMsg(True, "Invalid user: %s" % user)

        for l in levels:
            nu = UserLevel()
            nu.user_id = usr.id
            nu.level = l

        Session.commit()

        return vaultMsg(False, "Levels granted successfully")

    @authenticated_user
    def sflvault_addmachine(self, authtok, customer_id, name, fqdn, ip, location, notes):
        
        n = Machine()
        n.customer_id = int(customer_id)
        n.created_time = datetime.now()
        n.name = name
        n.fqdn = fqdn
        n.ip = ip
        n.location = location
        n.notes = notes

        Session.commit()

        return vaultMsg(False, "Machine added.", {'machine_id': n.id})


    @authenticated_user
    def sflvault_addservice(self, authtok, machine_id, parent_service_id, url,
                            level, secret, notes):

        # parent_service_id takes precedence over machine_id.
        if parent_service_id:
            try:
                parent = Service.query.get(parent_service_id)
                # No, you should be able to specify the machine, and not take
                # the parent's machine, since services can be inherited and
                # be on different machines (obvious example: ssh -> ssh, most
                # probably on two different machines)
                #machine_id = parent.machine_id
            except:
                return vaultMsg(True, "No such parent service ID.",
                                {'parent_service_id': parent_service_id})

        ns = Service()
        ns.machine_id = int(machine_id)
        ns.parent_service_id = parent_service_id or None
        ns.url = url
        ns.level = level
        (seckey, ciphertext) = encrypt_secret(secret)
        ns.secret = ciphertext
        ns.secret_last_modified = datetime.now()
        ns.notes = notes

        Session.commit()

        # TODO: get list of users to encrypt for (using levels assocs)
        lvls = UserLevel.query.filter_by(level=level).group_by('user_id').all()

        # Automatically add level to admin users, when creating a new level.
        if not len(lvls):
            us = User.query.filter_by(is_admin=True).all()
            for x in us:
                # Don't encode for users that aren't setup.
                if not x.pubkey:
                    continue
                ul = UserLevel()
                ul.user_id = x.id
                ul.level = level
                lvls.append(ul)
            Session.commit()

        userlist = []
        for lvl in lvls:
            # Don't encode for users that aren't setup.
            if not lvl.user.pubkey:
                continue

            # Encode for that user, store in UserCiphers
            nu = Usercipher()
            nu.service_id = ns.id
            nu.user_id = lvl.user_id

            g = lvl.user.elgamal()
            nu.stuff = serial_elgamal_msg(g.encrypt(seckey, randfunc(32)))
            del(g)
            
            userlist.append(lvl.user.username) # To return listing.

        Session.commit()

        del(seckey)

        return vaultMsg(False, "Service added.", {'service_id': ns.id,
                                                  'encrypted_for': userlist})

    @authenticated_admin
    def sflvault_deluser(self, authtok, username):
        
        try:
            u = User.query().filter_by(username=username).one()
        except:
            return vaultMsg(True, "User %s doesn't exist." % username)


        Session.delete(u)
        Session.commit()

        return vaultMsg(False, "User successfully deleted")


    @authenticated_user
    def sflvault_addcustomer(self, authtok, customer_name):
        nc = Customer()
        nc.name = customer_name
        nc.created_time = datetime.now()
        nc.created_user = self.sess['username']
        Session.commit()

        return vaultMsg(False, 'Customer added', {'customer_id': nc.id})


    @authenticated_user
    def sflvault_listcustomers(self, authtok):
        lst = Customer.query.all()

        out = []
        for x in lst:
            nx = {'id': x.id, 'name': x.name}
            out.append(nx)

        return vaultMsg(False, 'Here is the customer list', {'list': out})


    @authenticated_user
    def sflvault_listlevels(self, authtok):
        lvls = UserLevel.query.group_by(UserLevel.level).all()

        out = []
        for x in lvls:
            out.append(x.level)

        return vaultMsg(False, 'Here is the list of levels', {'list': out})


    @authenticated_user
    def sflvault_listmachines(self, authtok):
        lst = Machine.query.all()

        out = []
        for x in lst:
            nx = {'id': x.id, 'name': x.name, 'fqdn': x.fqdn, 'ip': x.ip,
                  'location': x.location, 'notes': x.notes,
                  'customer_id': x.customer_id, 'customer_name': x.customer.name}
            out.append(nx)

        return vaultMsg(False, "Here is the machines list", {'list': out})
    

    @authenticated_user
    def sflvault_listusers(self, authtok):
        lst = User.query.all()

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
                  'setup_expired': x.setup_expired()}
            out.append(nx)

        # Can use: datetime.fromtimestamp(x.created_stamp)
        # to get a datetime object back from the x.created_time
        return vaultMsg(False, "Here is the user list", {'list': out})
