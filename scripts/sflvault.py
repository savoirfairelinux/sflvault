#!/usr/bin/env python
# -=- encoding: utf-8 -=-

PROGRAM = "SFLvault"
VERSION = "0.1"

CONFIG_FILE = '~/.sflvault/config'

import optparse
import os
import sys
import xmlrpclib
from ConfigParser import ConfigParser
import pickle
import getpass
from Crypto.PublicKey import ElGamal
from Crypto.Cipher import AES, Blowfish
from Crypto.Util import randpool
from base64 import b64decode, b64encode
from decorator import decorator


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
# Authentication Failed exception
#
class AuthenticationError(StandardError):
    def __init__(self, message):
        """Sets an error message"""
        self.message = message
    def __str__(self):
        return self.message

class VaultError(StandardError):
    def __init__(self, message):
        """Sets an error message"""
        self.message = message
    def __str__(self):
        return self.message


#
### TODO: two functions that violate DRY principle, they are in lib/base.py
#
def vaultSerial(something):
    """Serialize with pickle.dumps + b64encode"""
    return b64encode(pickle.dumps(something))

def vaultUnserial(something):
    """Unserialize with b64decode + pickle.loads"""
    return pickle.loads(b64decode(something))

def vaultEncrypt(something, pw):
    """Encrypt using a password and Blowfish.

    something should normally be 8-bytes padded, but we add some '\0'
    to pad it.

    Most of the time anyway, we get some base64 stuff to encrypt, so
    it shouldn't pose a problem."""
    b = Blowfish.new(pw)
    return b64encode(b.encrypt(something + ((8 - (len(something) % 8)) * "\x00")))

def vaultDecrypt(something, pw):
    """Decrypt using Blowfish and a password

    Remove padding on right."""
    b = Blowfish.new(pw)
    return b.decrypt(b64decode(something)).rstrip("\x00")

def vaultReply(rep, errmsg="Error"):
    """Tracks the Vault reply, and raise an Exception on error"""

    if rep['error']:
        print "%s: %s" % (errmsg, rep['message'])
        raise VaultError(rep['message'])
    
    return rep


#
# authenticate decorator
#
@decorator
def authenticate(func, self, *args, **kwargs):
    """Login decorator

    self is there because it's called on class elements.
    """
    username = self.cfg.get('SFLvault', 'username')
    ### TODO: implement encryption of the private key.
    privkey_enc = self.cfg.get('SFLvault', 'key')
    privpass = getpass.getpass()
    privkey = vaultDecrypt(privkey_enc, privpass)
    privpass = randfunc(32)
    del(privpass)
    

    retval = self.vault.login(username)
    self.authret = retval
    if not retval['error']:
        # decrypt token.
        eg = ElGamal.ElGamalobj()
        (eg.p, eg.x) = vaultUnserial(privkey)
        privkey = randfunc(256)
        del(privkey)

        cryptok = eg.decrypt(vaultUnserial(retval['cryptok']))
        retval2 = self.vault.authenticate(username, vaultSerial(cryptok))
        self.authret = retval2
        
        if retval2['error']:
            raise AuthenticationError("Authentication failed: %s" % retval2['message'])
        else:
            self.authtok = retval2['authtok']
            print "Authentication successful"
    else:
        raise AuthenticationError("Authentication failed: %s" % retval['message'])

    return func(self, *args, **kwargs)


###
### On définit les fonctions qui vont traiter chaque sorte de requête.
###
class SFLvaultFunctions(object):
    """Class dealing with all the function calls to the Vault"""
    def __init__(self, cfg=None):
        """Set up initial configuration for function calls"""
        self.cfg = vaultConfigRead()
        self.authtok = ''
        self.authret = None
        self.vault = xmlrpclib.Server(self.cfg.get('SFLvault', 'url')).sflvault
        
    def _set_vault(self, url, save=False):
        """Set the vault's URL and optionally save it"""
        self.vault = xmlrpclib.Server(url).sflvault
        if save:
            self.cfg.set('SFLvault', 'url', url)


    def help(self, error = None):
        print "%s version %s" % (PROGRAM, VERSION)
        print "---------------------------------------------"
        print "Here is a quick overview of the commands:"
        print "  add-user"
        print "  setup         when originally creating your account"
        print "  del-user"
        print "  add-customer"
        print "  list-customers"
        print "  list-users"
        print "---------------------------------------------"
        print "Call: sflvault [command] --help for more details on"
        print "each of those commands."
        if (error):
            print "---"
            print "ERROR: %s" % error
        exit();

    @authenticate
    def add_user(self):
        # TODO: add support for --admin, to give admin privileges
        if (len(sys.argv) != 2):
            print "Usage: add-user [username]"
            sys.exit()
        username = sys.argv.pop(1)

        retval = vaultReply(self.vault.adduser(self.authtok, username),
                            "Error adding user")

        print "Vault says: %s" % retval['message']

    @authenticate        
    def add_customer(self):
        if (len(sys.argv) != 2):
            print 'Usage: add-customer ["customer name"]'
            sys.exit()
        customer_name = sys.argv.pop(1)

        retval = vaultReply(self.vault.addcustomer(self.authtok, customer_name),
                            "Error adding customer")

        print "Success: %s" % retval['message']

    def add_server(self):
        print "Do addserver"

    def grant(self):
        pass
    
    def setup(self):
        if (len(sys.argv) != 3):
            print "Usage: setup [username] [vault-url]"
            sys.exit()
        username = sys.argv.pop(1)
        url      = sys.argv.pop(1)
        self._set_vault(url, False)

        # Generate a new key:
        print "Generating new ElGamal key-pair..."
        eg = ElGamal.generate(1536, randfunc)

        # Marshal the ElGamal key
        pubkey = (eg.p, eg.g, eg.y)

        # TODO: make password CONFIRMATION
        print "Enter a password to secure your private key locally."
        privpass = getpass.getpass()

        print "Sending request to vault..."
        # Send it to the vault, with username
        retval = vaultReply(self.vault.setup(username, vaultSerial(pubkey)),
                            "Setup failed")

        # If Vault sends a SUCCESS, save all the stuff (username, url)
        # and encrypt privkey locally (with Blowfish)
        print "Vault says: %s" % retval['message']

        # Save all (username, url)
        # Encrypt privkey locally (with Blowfish)
        self.cfg.set('SFLvault', 'username', username)
        self._set_vault(url, True)
        # p and x form the private key
        self.cfg.set('SFLvault', 'key', vaultEncrypt(vaultSerial((eg.p, eg.x)), privpass))
        privpass = randfunc(32)
        eg.p = randfunc(32)
        eg.x = randfunc(32)
        del(eg)
        del(privpass)

        vaultConfigWrite(self.cfg)
        print "Saving settings..."

    
    def del_user(self):
        pass
    
    def search(self):
        print "Do search, and show and help to select."

    def show(self):
        print "Search using xmlrpc:show(), with the service_id, and DECRYPT"

    @authenticate
    def list_users(self):
        if (len(sys.argv) != 1):
            print 'Usage: list-users'
            sys.exit()

        # Receive: [{'id': x.id, 'username': x.username,
        #            'created_time': x.created_time,
        #            'is_admin': x.is_admin,
        #            'setup_expired': x.setup_expired()}
        #            {}, {}, ...]
        #    
        retval = vaultReply(self.vault.listusers(self.authtok),
                            "Failed listing users")

        print "User list (with creation date):"
        for x in retval['list']:
            add = ''
            if x['is_admin']:
                add += ' [is admin]'
            if not x['setup_expired']:
                add += ' [in setup process]'
            print "   %s (#%d)%s - %s" % (x['username'], x['id'], add, x['created_ctime'])

        

    @authenticate
    def list_customers(self):
        if (len(sys.argv) != 1):
            print 'Usage: list-customers'
            sys.exit()

        retval = vaultReply(self.vault.listcustomers(self.authtok),
                            "Error listing customers")

        # Receive a list: [{'id': '%d',
        #                   'name': 'blah'},
        #                  {'id': '%d',
        #                   'name': 'blah2'}]
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
except AttributeError, e:
    print e
    getattr(f, 'help')("Invalid action: %s" % action)
except AuthenticationError:
    raise
except VaultError:
    raise
