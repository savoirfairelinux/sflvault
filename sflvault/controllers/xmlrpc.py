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


def _setupSessions(self):
    """DRY out _setSession and _getSession"""
    if not g.has_key('vaultSessions'):
        g['vaultSessions'] = {}

def _setSession(self, authtok, value):
    """Sets in 'g.vaultSessions':
    {authtok1: {'username':  , 'timeout': datetime}, authtok2: {}..}
    
    """
    self._setupSessions();

    g['vaultSessions'][authtok] = value;
        
def _getSession(self, authtok):
    """Return the values associated with a session"""
    self._setupSessions();

    if not g['vaultSessions'].has_key(authtok):
        return None

    if not g['vaultSessions'][authtok].has_key('timeout'):
        g['vaultSessions'][authtok]['timeout'] = datetime.now() = timedelta(0, SESSION_TIMEOUT)
    
    if g['vaultSessions'][authtok]['timeout'] < datetime.now():
        del(g['vaultSessions'][authtok])
        return None

    return g['vaultSessions'][authtok]


##
## See: http://wiki.pylonshq.com/display/pylonsdocs/Using+the+XMLRPCController
##
class XmlrpcController(XMLRPCController):


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


    def sflvault_adduser(self, username):
        # TODO: authenticate
        # TODO: verifier si l'usager loggé est ADMIN

        if (User.query().filter_by(username=username).count()):
            return vaultMsg(True, 'User %s already exists.' % username)
        
        n = User()
        n.waiting_setup =  datetime.now() + timedelta(0, SETUP_TIMEOUT)
        n.username = username
        n.created_time = datetime.now()
        # Une manière d'ajouter un utilisateur 'ADMIN'.

        Session.commit()

        return vaultMsg(False, 'User added. User has a delay of %d seconds to invoke a "setup" command' % SETUP_TIMEOUT)


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
            return vaultMsg(True, 'User unknown')

        if u.logging_timeout < datetime.now():
            return vaultMsg(True, 'Login token expired')

        # str() necessary, to convert buffer to string.
        if vaultUnserial(cryptok) != str(u.logging_token):
            return vaultMsg(True, 'Authentication failed')
        else:
            # TODO: generate session token, and return authtok
            return vaultMsg(False, 'Authentication successful', {'authtok': 'token'})

    def sflvault_addcustomer(self, authtok, customer_name):
        pass

    def sflvault_listcustomers(self, authtok):
        lst = 
