#!/usr/bin/env python
# -=- encoding: utf-8 -=-

PROGRAM = "SFLvault"
VERSION = "0.1"

SERVER = 'http://localhost:5000/vault/rpc'
CONFIG_FILE = '~/.sflvault/config'

import optparse
import os
import sys
import xmlrpclib
from ConfigParser import ConfigParser
import pickle
from Crypto.PublicKey import ElGamal
from Crypto.Cipher import AES, Blowfish
from Crypto.Util import randpool
from base64 import b64decode, b64encode

from pprint import pprint


### Setup variables and functions
#
# Setup default action = help
#
action = 'help'
if (len(sys.argv) > 1):
    # Take out the action.
    action = sys.argv.pop(1)
    if (action in ['-h', '--help']):
        action = 'help'

    # Fix for functions
    action = action.replace('-', '_')

#
# Config file setup
#
def vaultConfigCheck():
    """Checks for ownership and modes for all paths and files, à-la SSH"""
    fullfile = os.path.expanduser(CONFIG_FILE)
    fullpath = os.path.dirname(fullfile)
    
    if not os.path.exists(fullpath):
        os.makedirs(fullpath, mode=0700)

    if not os.stat(fullpath)[0] & 0700:
        print "Modes for %s must be 0700 (-rwx------)" % fullpath
        sys.exit()

    if not os.path.exists(fullfile):
        fp = open(fullfile, 'w')
        fp.write("[SFLvault]\n")
        fp.close()
        os.chmod(fullfile, 0600)
        
    if not os.stat(fullfile)[0] & 0600:
        print "Modes for %s must be 0600 (-rw-------)" % fullfile
        sys.exit()

    return True

def vaultConfigRead():
    """Return the ConfigParser object, fully loaded"""
    vaultConfigCheck()
    
    cfg = ConfigParser()
    fp = open(os.path.expanduser(CONFIG_FILE), 'r')
    cfg.readfp(fp)
    fp.close()

    if not cfg.has_section('SFLvault'):
        cfg.add_section('SFLvault')

    if not cfg.has_option('SFLvault', 'username'):
        cfg.set('SFLvault', 'username', '')
    
    if not cfg.has_option('SFLvault', 'url'):
        cfg.set('SFLvault', 'url', '')

    return cfg

def vaultConfigWrite(cfg):
    """Write the ConfigParser element to disk."""
    fp = open(os.path.expanduser(CONFIG_FILE), 'w')
    cfg.write(fp)
    fp.close()

# global cfg object
cfg = vaultConfigRead()



#
# Command line parser
#
parser = optparse.OptionParser()



#
# Random number generators setup
#
pool = randpool.RandomPool()
pool.stir()
pool.randomize()
randfunc = pool.get_bytes # We'll use this func for most of the random stuff


#
# XML-RPC server setup.
#
## TODO: Use the config version, complain only if the 'action' isn't in
## ['help', 'setup', ??]
srv = xmlrpclib.Server(SERVER)



#
# Helper functions
#
authtok = None  # global value
def authenticate():
    username = cfg.get('SFLvault', 'username')
    ### TODO: implement encryption of the private key.
    privkey = cfg.get('SFLvault', 'key')

    retval = srv.sflvault.login(username)
    if not retval['error']:
        # decrypt token.
        eg = ElGamal.ElGamalobj()
        (eg.p, eg.x) = vaultUnserial(privkey)

        cryptok = eg.decrypt(vaultUnserial(retval['cryptok']))
        retval2 = srv.sflvault.authenticate(username, vaultSerial(cryptok))

        if retval2['error']:
            print "Authentication failed"
        else:
            authtok = retval2['authtok']
            print "Authentication successful"
    else:
        print "Authentication failed"

    return authtok

### TODO: two functions that violate DRY principle, they are in lib/base.py
def vaultSerial(something):
    """Serialize with pickle.dumps + b64encode"""
    return b64encode(pickle.dumps(something))

def vaultUnserial(something):
    """Unserialize with b64decode + pickle.loads"""
    return pickle.loads(b64decode(something))


###
### On définit les fonctions qui vont traiter chaque sorte de requête.
###
class SFLvaultFunctions(object):
    def help(self, error = None):
        print "%s version %s" % (PROGRAM, VERSION)
        print "---------------------------------------------"
        print "Here is a quick overview of the commands:"
        print "  adduser       add a user"
        print "  deluser       remove a user"
        print "  [add more]    yes please"
        print "---------------------------------------------"
        print "Call: sflvault [command] --help for more details on"
        print "each of those commands."
        if (error):
            print "---"
            print "ERROR: %s" % error
        exit();
    
    def adduser(self):
        if (len(sys.argv) != 2):
            print "Usage: adduser [username]"
            sys.exit()
        username = sys.argv.pop(1)

        if not authenticate():
            sys.exit()

        retval = srv.sflvault.adduser(authtok, username)

        if (retval['error']):
            print "Vault error: %s" % retval['message']
        else:
            print "Vault says: %s" % retval['message']

    def addcustomer(self):
        if (len(sys.argv) != 2):
            print 'Usage: add-customer ["customer name"]'
            sys.exit()
        customer_name = sys.argv.pop(1)

        authtok = authenticate()
        if not authtok:
            sys.exit()

        retval = srv.sflvault.addcustomer(authtok, customer_name)

        if (retval['error']):
            print "Error adding customer: %s" % retval['message']
        else:
            print "Success: %s" % retval['message']

    def addserver(self):
        print "Do addserver"

    def grant(self):
        pass
    
    def setup(self):
        if (len(sys.argv) != 3):
            print "Usage: setup [username] [vault-url]"
            sys.exit()
        username = sys.argv.pop(1)
        url      = sys.argv.pop(1)
        ## TODO: use the 'url', and not the hard-coded one.

        # Generate a new key:
        print "Generating new ElGamal key-pair..."
        eg = ElGamal.generate(1536, randfunc)

        # Marshal the ElGamal key
        pubkey = (eg.p, eg.g, eg.y)

        print "Sending request to vault..."
        # Send it to the vault, with username
        retval = srv.sflvault.setup(username, vaultSerial(pubkey))

        # If Vault sends a SUCCESS, save all the stuff (username, url)
        # and encrypt privkey locally (with Blowfish)
        print "Vault says: %s" % retval['message']

        if not (retval['error']):
            # Save all (username, url)
            # Encrypt privkey locally (with Blowfish)
            cfg.set('SFLvault', 'username', username)
            cfg.set('SFLvault', 'url', url)
            # p and x form the private key
            cfg.set('SFLvault', 'key', vaultSerial((eg.p, eg.x)))
            vaultConfigWrite(cfg)
            print "Saving settings..."

    
    def deluser(self):
        pass
    
    def connect(self):
        authenticate()
    
    def search(self):
        print "Do search, and show and help to select."

    def show(self):
        print "Search using xmlrpc:show(), with the service_id, and DECRYPT"
        
    def list_users(self):
        print "Do addserver"

    def list_customers(self):
        if (len(sys.argv) != 1):
            print 'Usage: list-customers'
            sys.exit()

        authtok = authenticate()
        if not authtok:
            sys.exit()

        retval = srv.sflvault.listcustomers(authtok)

        if retval['error']:
            print "Error listing customers: %s" % retval['message']

        print "Customer list:"
        for x in retval['list']:
            print "ID: %04d  -  %s" % (x['id'], x['name'])
            



###
### Execute requested command-line command
###
f = SFLvaultFunctions()

# Call the appropriate function of the 'f' object, according to 'action'

try:
    getattr(f, action)()
except AttributeError:
    getattr(f, 'help')("Unknown action: %s" % action)
