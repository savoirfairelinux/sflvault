# -=- encoding: utf-8 -=-
import logging


import xmlrpclib
#import pylons
#from pylons import request
from pylons.controllers import XMLRPCController
from Crypto.PublicKey import ElGamal
from Crypto.Cipher import AES
from Crypto.Util import randpool
from base64 import b64decode, b64encode
from datetime import *
import pickle
import time as stdtime

from sflvault.lib.base import *
from sflvault.model import *

log = logging.getLogger(__name__)

# Random number generators setup
pool = randpool.RandomPool()
pool.stir()
pool.randomize()
randfunc = pool.get_bytes # We'll use this func for most of the random stuff

#
# Configuration
#
# TODO: make those configurable
SETUP_TIMEOUT = 60
SESSION_TIMEOUT = 300




##
## See: http://wiki.pylonshq.com/display/pylonsdocs/Using+the+XMLRPCController
##
class XmlrpcController(XMLRPCController):
    """All XML-RPC calls to control and query the Vault"""

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
        u.logging_token = rnd

        Session.commit()

        e = u.elgamal()
        cryptok = vaultSerial(e.encrypt(rnd, randfunc(32)))
        return vaultMsg(False, 'Authenticate please', {'cryptok': cryptok})

    def sflvault_authenticate(self, username, cryptok):
        try:
            u = User.query().filter_by(username=username).one()
        except:
            return vaultMsg(True, 'Invalid user')

        if u.logging_timeout < datetime.now():
            return vaultMsg(True, 'Login token expired')

        # str() necessary, to convert buffer to string.
        if vaultUnserial(cryptok) != str(u.logging_token):
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

        return vaultMsg(False, 'User added. User has a delay of %d seconds to invoke a "setup" command' % SETUP_TIMEOUT)


    @authenticated_user
    def sflvault_addserver(self, authtok, customer_id, name, fqdn, ip, location, notes):
        
        n = Server()
        n.customer_id = int(customer_id)
        n.created_time = datetime.now()
        n.name = name
        n.fqdn = fqdn
        n.ip = ip
        n.location = location
        n.notes = notes

        Session.commit()

        return vaultMsg(False, "Server added.", {'server_id': n.id})


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

        return vaultMsg(False, 'Customer added as no. %d' % nc.id)


    @authenticated_user
    def sflvault_listcustomers(self, authtok):
        lst = Customer.query.all()

        out = []
        for x in lst:
            nx = {'id': x.id, 'name': x.name}
            out.append(nx)

        return vaultMsg(False, 'Here is the customer list', {'list': out})


    @authenticated_user
    def sflvault_listservers(self, authtok):
        lst = Server.query.all()

        out = []
        for x in lst:
            nx = {'id': x.id, 'name': x.name, 'fqdn': x.fqdn, 'ip': x.ip,
                  'location': x.location, 'notes': x.notes,
                  'customer_id': x.customer_id, 'customer_name': x.customer.name}
            out.append(nx)

        return vaultMsg(False, "Here is the servers list", {'list': out})
    

    @authenticated_user
    def sflvault_listusers(self, authtok):
        lst = User.query.all()

        out = []
        for x in lst:
            # perhaps add the pubkey ?
            if x.created_time:
                ctme = x.created_time.ctime()
                stmp = stdtime.mktime(x.created_time.timetuple())
            else:
                ctme = '[unknown]'
                stmp = 0
                
            nx = {'id': x.id, 'username': x.username,
                  'created_ctime': ctme,
                  'created_stamp': stmp,
                  'is_admin': x.is_admin,
                  'setup_expired': x.setup_expired()}
            out.append(nx)

        # Can use: datetime.fromtimestamp(x.created_stamp)
        # to get a datetime object back from the x.created_time
        return vaultMsg(False, "Here is the user list", {'list': out})
