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
from datetime import *

from pprint import pprint


### Setup variables and functions

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
    return b64encode(b.encrypt(something + (((8 - (len(something) % 8)) % 8) * "\x00")))

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
# Functions to allow writing aliases, or m#123 IDs, everywhere where
# a service ID, a server ID, a customer ID or a user ID is required.
#
class vaultIdFormateError(Exception):
    """When bad parameters are passed to vaultId"""
    pass

def vaultId(id, prefix):
    """Return an integer value for a given VaultID.

    A VaultID can be one of the following:

      123   - treated as is, and assume to be of type `prefix`.
      m#123 - checked against `prefix`, otherwise raise an exception.
      alias - checked against `prefix` and alias list, returns an int
              value, or raise an exception.
    """
    #prefixes = ['m', 'u', 's', 'c'] # Machine, User, Service, Customer
    #if prefix not in prefixes:
    #    raise ValueError("Bad prefix for id %s (prefix given: %s)" % (id, prefix))

    # If it's only a numeric, assume it is of type 'prefix'.
    try:
        tmp = int(id)
        return tmp
    except:
        pass

    # Match the m#123 formats..
    tid = re.match(r'(.)#(\d+)', id)
    if tid:
        if tid.group(1) != prefix:
            raise vaultIdFormatError("Bad prefix for VaultID, context requires '%s': %s" % (prefix, id))
        return int(tid.group(2))

    # TODO: Check for aliases    
    raise vaultIdFormatError("Invalid alias of bad VaultID format: %s" % id)
    

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
    privpass = getpass.getpass("Vault password: ")
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
class SFLvault(object):
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


    @authenticate
    def add_user(self, username, admin=False):
        # TODO: add support for --admin, to give admin privileges

        retval = vaultReply(self.vault.adduser(self.authtok, username, admin),
                            "Error adding user")

        print "Success: %s" % retval['message']


    @authenticate
    def del_user(self, username):
        retval = vaultReply(self.vault.deluser(self.authtok, username),
                            "Error removing user")

        print "Success: %s" % retval['message']


    @authenticate        
    def add_customer(self, customer_name):
        retval = vaultReply(self.vault.addcustomer(self.authtok, customer_name),
                            "Error adding customer")

        print "Success: %s" % retval['message']


    @authenticate
    def add_server(self, customer_id, name, fqdn, ip, location, notes):
        """Add a server to the database."""
        # customer_id REQUIRED
        retval = vaultReply(self.vault.addserver(self.authtok, int(customer_id),
                                                 name or '', fqdn or '', ip or '',
                                                 location or '', notes or ''),
                            "Error adding server")
        print "Success: %s" % retval['message']
        print "New machine ID: m#%d" % retval['server_id']


    @authenticate
    def add_service(self, server_id, url, port, loginname, type, level, secret, notes):
        #levels = [x.strip() for x in level.split(',')]
        # TODO: encrypter le secret ??
        retval = vaultReply(self.vault.addservice(self.authtok, int(server_id), url, port or '', loginname or '', type or '', level, secret, notes or ''),
                            "Error adding service")

        print "Success: %s" % retval['message']
        print "New service ID: s#%d" % retval['service_id']

    def grant(self):
        pass
    
    def setup(self, username, vault_url):
        self._set_vault(vault_url, False)

        # Generate a new key:
        print "Generating new ElGamal key-pair..."
        eg = ElGamal.generate(1536, randfunc)

        # Marshal the ElGamal key
        pubkey = (eg.p, eg.g, eg.y)

        # TODO: make password CONFIRMATION
        privpass = getpass.getpass("Enter a password to secure your private key locally: ")

        print "Sending request to vault..."
        # Send it to the vault, with username
        retval = vaultReply(self.vault.setup(username, vaultSerial(pubkey)),
                            "Setup failed")

        # If Vault sends a SUCCESS, save all the stuff (username, vault_url)
        # and encrypt privkey locally (with Blowfish)
        print "Vault says: %s" % retval['message']

        # Save all (username, vault_url)
        # Encrypt privkey locally (with Blowfish)
        self.cfg.set('SFLvault', 'username', username)
        self._set_vault(vault_url, True)
        # p and x form the private key
        self.cfg.set('SFLvault', 'key', vaultEncrypt(vaultSerial((eg.p, eg.x)), privpass))
        privpass = randfunc(32)
        eg.p = randfunc(32)
        eg.x = randfunc(32)
        del(eg)
        del(privpass)

        vaultConfigWrite(self.cfg)
        print "Saving settings..."

    
    def search(self):
        print "Do search, and show and help to select."

    def show(self):
        print "Search using xmlrpc:show(), with the service_id, and DECRYPT"

    @authenticate
    def list_users(self):
        # Receive: [{'id': x.id, 'username': x.username,
        #            'created_time': x.created_time,
        #            'is_admin': x.is_admin,
        #            'setup_expired': x.setup_expired()}
        #            {}, {}, ...]
        #    
        retval = vaultReply(self.vault.listusers(self.authtok),
                            "Error listing users")

        print "User list (with creation date):"
        for x in retval['list']:
            add = ''
            if x['is_admin']:
                add += ' [is admin]'
            if not x['setup_expired']:
                add += ' [in setup process]'
            # dt = datetime.strptime(x['created_stamp'], "
            #created =
            # TODO: load the xmlrpclib.DateTime object into something more fun
            #       to deal with! Some day..
            print "u#%d\t%s\t%s %s" % (x['id'], x['username'],
                                       x['created_stamp'], add)


    @authenticate
    def list_servers(self, verbose=False):
        retval = vaultReply(self.vault.listservers(self.authtok),
                            "Error listing servers")

        print "Server list (machines):"

        oldcid = 0
        for x in retval['list']:
            if oldcid != x['customer_id']:
                print "%s (c#%d)" % (x['customer_name'], x['customer_id'])
                oldcid = x['customer_id']
            print "\tm#%d\t%s (%s)" % (x['id'], x['name'], x['fqdn'] or x['ip'])
            if verbose:
                print "\t\tLocation: %s" % x['location'].replace('\n', '\t\t\n')
                print "\t\tNotes: %s" % x['notes'].replace('\n', '\t\t\n')
                print '-' * 76


    @authenticate
    def list_customers(self):
        retval = vaultReply(self.vault.listcustomers(self.authtok),
                            "Error listing customers")

        # Receive a list: [{'id': '%d',
        #                   'name': 'blah'},
        #                  {'id': '%d',
        #                   'name': 'blah2'}]
        print "Customer list:"
        for x in retval['list']:
            print "c#%d\t%s" % (x['id'], x['name'])



class SFLvaultParserError(Exception):
    """For invalid options on the command line"""
    pass

class SFLvaultParser(object):
    """Parse command line arguments, and call SFLvault commands
    on them."""
    def __init__(self, argv, vault = None):
        """Setup the SFLvaultParser object.

        argv - arguments from the command line
        sflvault - SFLvault object (optional)"""
        self.parser = optparse.OptionParser(usage=optparse.SUPPRESS_USAGE)
        self.argv = argv[1:] # Bump the first (command name)
        self.args = []       # Used after a call to _parse()
        self.opts = object() #  idem.
        
        # Use the specified, or create a new one.
        self.vault = (vault or SFLvault())

        # Setup default action = help
        action = 'help'
        if (len(self.argv)):
            # Take out the action.
            action = self.argv.pop(0)
            if (action in ['-h', '--help']):
                action = 'help'

            # Fix for functions
            action = action.replace('-', '_')
        # Check the first parameter, if it's in the local object.

        # Call it or show the help.
        if hasattr(self, action):
            self.action = action
            try:
                getattr(self, action)()
            except SFLvaultParserError, e:
                self.help(cmd=action, error=e)
        else:
            self.help()
        

    def _parse(self):
        """Parse the command line options, and fill self.opts and self.args"""
        (self.opts, self.args) = self.parser.parse_args(args=self.argv)


    def help(self, cmd = None, error = None):
        """Print this help.

        You can use:
        
          help [command]

        to get further help for `command`."""

        print "%s version %s" % (PROGRAM, VERSION)
        print "---------------------------------------------"

        if not cmd:
            print "Here is a quick overview of the commands:"
            # TODO: go around all the self. attributes and display docstrings
            #       and give coherent help for every function if specified.
            #       all those not starting with _.
            for x in dir(self):
                if not x.startswith('_') and callable(getattr(self, x)):
                    doc = getattr(self, x).__doc__
                    if doc:
                        doc = doc.split("\n")[0]
                    else:
                        doc = '[n/a]'
                
                    print "  %s%s%s" % (x.replace('_','-'),
                                        (25 - len(x)) * ' ',
                                        doc)
            print "---------------------------------------------"
            print "Call: sflvault [command] --help for more details on each of those commands."
        elif not cmd.startswith('_') and callable(getattr(self, cmd)):
            readcmd = cmd.replace('_','-')

            doc = getattr(self, cmd).__doc__
            if doc:
                print "Help for command: %s" % readcmd
                print "---------------------------------------------"
                print doc
            else:
                print "No documentation available for `%s`." % readcmd

            print ""
            self.parser.parse_args(args=['--help'])
        else:
            print "No such command"

        print "---------------------------------------------"
            
        if (error):
            print "ERROR calling %s: %s" % (cmd, error)
        return
            

    def add_user(self):
        """Add a user to the Vault.

        Syntax:

          add-user [-a] [--admin] username

        Optionally flag user as administrator."""

        # Parse the argv as needed
        self.parser.add_option('-a', '--admin', dest="is_admin",
                               action="store_true", default=False,
                               help="Give admin privileges to the added user")

        self._parse()

        if (len(self.args) != 1):
            raise SFLvaultParserError("Invalid number of arguments")
        
        username = self.args[0]
        admin = self.opts.is_admin

        self.vault.add_user(username, admin)


    def add_customer(self):
        """Add a new customer to the Vault's database."""
        self.parser.set_usage('add-customer "customer name"')
        self._parse()
        
        if (len(self.args) != 1):
            raise SFLvaultParserError('Invalid number of arguments')

        customer_name = self.args[0]

        self.vault.add_customer(customer_name)


    def del_user(self):
        """Delete an existing user."""
        self.parser.set_usage("del-user username")
        self._parse()

        if (len(self.args) != 1):
            raise SFLvaultParserError("Invalid number of arguments")

        username = self.args[0]

        self.vault.del_user(username)


    def add_server(self):
        """Add a server (machine) to the Vault's database."""
        self.parser.set_usage("add-server [options]")
        self.parser.add_option('-c', '--customer', dest="customer_id",
                               help="Customer id, as 'c#123' or '123'")
        self.parser.add_option('-n', '--name', dest="name",
                               help="Server name, used for display everywhere")
        self.parser.add_option('-d', '--fqdn', dest="fqdn", default='',
                               help="Fully qualified domain name, if available")
        self.parser.add_option('-i', '--ip', dest="ip", default='',
                               help="Machine's IP address, in order to access itfrom it's hierarchical position")
        self.parser.add_option('-l', '--location', dest="location", default='',
                               help="Machine's physical location, position in racks, address, etc..")
        self.parser.add_option('--notes', dest="notes",
                               help="Notes about the machine, references, URLs.")

        self._parse()

        if not self.opts.name:
            raise SFLvaultParserError("Required parameter 'name' omitted")
        
        ## TODO: make a list-customers and provide a selection using arrows or
        #        or something alike.
        if not self.opts.customer_id:
            raise SFLvaultParserError("Required parameter 'customer' omitted")

        o = self.opts
        self.vault.add_server(vaultId(o.customer_id, 'c'), o.name, o.fqdn,
                              o.ip, o.location, o.notes)


    def add_service(self):
        """Add a service to a particular server in the Vault's database.

        The secret/password/authentication key will be asked in the
        interactive prompt."""
        self.parser.add_option('-s', '--server', dest="server_id",
                               help="Service will be attached to server, as 'm#123' or '123'")
        self.parser.add_option('-u', '--url', dest="url",
                               help="Service URL, full proto://fqdn.example.org/path, WITHOUT the secret.")
        self.parser.add_option('-t', '--type', dest="type",
                               help="Service type (ssh, ftp, web)")
        self.parser.add_option('-p', '--port', dest="port", default='',
                               help="Service port, if different from the default")
        self.parser.add_option('-l', '--login', '--username', dest="loginname",
                               help="Username/login name for service.")
        self.parser.add_option('-v', '--level', dest="level", default='',
                               help="Access level (access group) for this service. Use list-levels to get a complete list of access levels.")
        self.parser.add_option('--notes', dest="notes",
                               help="Notes about the service, references, URLs.")

        self._parse()

        if not self.opts.url:
            raise SFLvaultParserError("Required parameter 'url' omitted")
        
        ## TODO: make a list-customers and provide a selection using arrows or
        #        or something alike.
        if not self.opts.server_id:
            raise SFLvaultParserError("Required parameter 'server' omitted")

        secret = getpass.getpass("Enter service secret (password): ")

        o = self.opts
        self.vault.add_service(vaultId(o.server_id, 'm'), o.url, o.port,
                               o.loginname, o.type, o.level, secret, o.notes)


    def list_customers(self):
        """List existing customers.

        This option takes no argument, it just lists customers with their IDs."""
        self._parse()
        
        if len(self.args):
            raise SFLvaultParserError('Invalid number of arguments')

        self.vault.list_customers()

    def list_users(self):
        """List existing users.

        This option takes no argument, it lists the current users and their
        privileges."""
        self._parse()

        if len(self.args):
            raise SFLvaultParserError("Invalid number of arguments")

        self.vault.list_users()


    def list_servers(self):
        """List existing servers.

        This command will list all servers in the Vault's database."""
        ## TODO: add support for listing only servers of a certain c#id
        #        (customer_id)
        self.parser.add_option('-v', '--verbose', action="store_true",
                               dest='verbose', default=False,
                               help="Enable verbose output (location and notes)")
        self._parse()

        if len(self.args):
            raise SFLvaultParserError("Invalid number of arguments")

        self.vault.list_servers(self.opts.verbose)
        

    def setup(self):
        """Setup a new user on the vault.

        Call this after an admin has called `add-user` on the vault.
        
        Syntax: setup [username] [vault_url]

        username  - the username used in the `add-user` call.
        vault_url - the URL (http://example.org:port/vault/rpc) to the
                    Vault"""
        self._parse()
        
        if len(self.args) != 2:
            raise SFLvaultParserError("Invalid number of arguments")

        username = self.args[0]
        url      = self.args[1]

        self.vault.setup(username, url)
        
        
###
### Execute requested command-line command
###    
if __name__ == "__main__":

    # Call the appropriate function of the 'f' object, according to 'action'
    
    try:
        f = SFLvaultParser(sys.argv)
    except AuthenticationError:
        raise
    except VaultError:
        #raise
        pass
    except xmlrpclib.Fault, e:
        # On is_admin check failed, on user authentication failed.
        print "Fault: %s" % e.faultString
7
