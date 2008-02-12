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


##
## See: http://wiki.pylonshq.com/display/pylonsdocs/Using+the+XMLRPCController
##
class XmlrpcController(XMLRPCController):

    def sflvault_setup(self, username, pubkey):

        # First, remove ALL users that have waiting_setup expired, where
        # waiting_setup isn't NULL.
        Session.delete(User.query().filter(User.waiting_setup != None).filter(User.waiting_setup < datetime.now()))
        raise RuntimeError
        cnt = User.query().count()
        
        u = User.query().filter_by(username=username).first()


        if (cnt):
            if (not u):
                return {'error': True, 'message': 'No such user %s' % username}
        
            if (u.setup_expired()):
                return {'error': True, 'message': 'Setup expired for user %s' % username}

        # Ok, let's save the things and reset waiting_setup.
        u.waiting_setup = None
        u.pubkey = pubkey

        Session.commit()

        return {'error': False, 'message': 'User setup complete for %s' % username}


    def sflvault_adduser(self, username):
        # TODO: authenticate
        # TODO: verifier si l'usager loggé est ADMIN
        # TODO: rendre configurable SETUP_TIMEOUT
        SETUP_TIMEOUT = 60

        if (User.query().filter_by(username=username).count()):
            return {'error': True, 'message': 'User %s already exists.' % username}
        
        n = User()
        n.waiting_setup =  datetime.now() + timedelta(0, SETUP_TIMEOUT)
        n.username = username
        n.created_time = datetime.now()
        # Une manière d'ajouter un utilisateur 'ADMIN'.

        Session.commit()

        return {'error': False, 'message': 'User added. User has a delay of %d seconds to invoke a "setup" command' % SETUP_TIMEOUT}


    def sflvault_authenticate(self):
        return [u.username, u.is_admin, b64encode(randfunc(32))]
        return "Hello again"
