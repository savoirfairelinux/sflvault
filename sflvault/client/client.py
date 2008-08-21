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


PROGRAM = "SFLvault"
VERSION = "0.5.0"

CONFIG_FILE = '~/.sflvault/config'

import optparse
import os
import re
import sys
import xmlrpclib
from ConfigParser import ConfigParser
import getpass
from Crypto.PublicKey import ElGamal
from base64 import b64decode, b64encode
from decorator import decorator
from datetime import *

from pprint import pprint
from sflvault.lib.common.crypto import *
from sflvault.client.utils import *
from sflvault.client import remoting


### Setup variables and functions


def vaultReply(rep, errmsg="Error"):
    """Tracks the Vault reply, and raise an Exception on error"""

    if rep['error']:
        print "%s: %s" % (errmsg, rep['message'])
        raise VaultError(rep['message'])
    
    return rep


#
# authenticate decorator
#
def authenticate(keep_privkey=False):
    def do_authenticate(func, self, *args, **kwargs):
        """Login decorator
        
        self is there because it's called on class elements.
        """
        username = self.cfg.get('SFLvault', 'username')
        ### TODO: implement encryption of the private key.
        try:
            privkey_enc = self.cfg.get('SFLvault', 'key')
        except:
            raise VaultConfigurationError("No private key in local config, init with: setup username vault-url")
        
        privpass = self.getpassfunc()
        try:
            privkey = decrypt_privkey(privkey_enc, privpass)
        except DecryptError, e:
            print "[SFLvault] Invalid pass-phrase"
            return False
            
        privpass = randfunc(32)
        del(privpass)

        # TODO: maybe check when we're already logged in, and check
        #       the timeout.
        # TODO: check also is the privkey (ElGamal obj) has been cached
        #       in self.privkey (when invoked with keep_privkey)
        retval = self.vault.login(username)
        self.authret = retval
        if not retval['error']:
            # decrypt token.
            eg = ElGamal.ElGamalobj()
            (eg.p, eg.x, eg.g, eg.y) = unserial_elgamal_privkey(privkey)
            privkey = randfunc(len(privkey))
            del(privkey)

            # When we ask to keep the privkey, keep the ElGamal obj.
            if keep_privkey:
                self.privkey = eg

            cryptok = eg.decrypt(unserial_elgamal_msg(retval['cryptok']))
            retval2 = self.vault.authenticate(username, b64encode(cryptok))
            self.authret = retval2
        
            if retval2['error']:
                raise AuthenticationError("Authentication failed: %s" % retval2['message'])
            else:
                self.authtok = retval2['authtok']
                print "Authentication successful"
        else:
            raise AuthenticationError("Authentication failed: %s" % retval['message'])

        return func(self, *args, **kwargs)

    return decorator(do_authenticate)

###
### On définit les fonctions qui vont traiter chaque sorte de requête.
###
class SFLvaultClient(object):
    """Class dealing with all the function calls to the Vault"""
    def __init__(self, cfg=None):
        """Set up initial configuration for function calls"""
        # The function to call upon @authenticate to get password from user.
        self.getpassfunc = self._getpass
        # Load configuration
        self.config_read()
        self.authtok = ''
        self.authret = None
        # Set the default route to the Vault
        url = self.cfg.get('SFLvault', 'url')
        if url:
            self.vault = xmlrpclib.Server(url).sflvault

    def _getpass(self):
        """Default function to get password from user, for authentication."""
        return getpass.getpass("Vault password: ")


    def config_check(self):
        """Checks for ownership and modes for all paths and files, à-la SSH"""
        fullfile = os.path.expanduser(CONFIG_FILE)
        fullpath = os.path.dirname(fullfile)
    
        if not os.path.exists(fullpath):
            os.makedirs(fullpath, mode=0700)

        if not os.stat(fullpath)[0] & 0700:
            ### TODO: RAISE EXCEPTION INSTEAD
            print "Modes for %s must be 0700 (-rwx------)" % fullpath
            sys.exit()

        if not os.path.exists(fullfile):
            fp = open(fullfile, 'w')
            fp.write("[SFLvault]\n")
            fp.close()
            os.chmod(fullfile, 0600)
        
        if not os.stat(fullfile)[0] & 0600:
            # TODO: raise exception instead.
            print "Modes for %s must be 0600 (-rw-------)" % fullfile
            sys.exit()

    def config_read(self):

        """Return the ConfigParser object, fully loaded"""
        self.config_check()
    
        self.cfg = ConfigParser()
        fp = open(os.path.expanduser(CONFIG_FILE), 'r')
        self.cfg.readfp(fp)
        fp.close()

        if not self.cfg.has_section('SFLvault'):
            self.cfg.add_section('SFLvault')

        if not self.cfg.has_section('Aliases'):
            self.cfg.add_section('Aliases')

        if not self.cfg.has_option('SFLvault', 'username'):
            self.cfg.set('SFLvault', 'username', '')
    
        if not self.cfg.has_option('SFLvault', 'url'):
            self.cfg.set('SFLvault', 'url', '')

    def config_write(self):
        """Write the ConfigParser element to disk."""
        fp = open(os.path.expanduser(CONFIG_FILE), 'w')
        self.cfg.write(fp)
        fp.close()

    def set_getpassfunc(self, func):
        """Set the function to ask for password.

        By default, it is set to _getpass, which asks for the password on the
        command line, but you can create a new function, that would for example
        pop-up a window, or use another mechanism to ask for password and continue
        authentication."""
        self.getpassfunc = func
        
    def _set_vault(self, url, save=False):
        """Set the vault's URL and optionally save it"""
        self.vault = xmlrpclib.Server(url).sflvault
        if save:
            self.cfg.set('SFLvault', 'url', url)


    def alias_add(self, alias, ptr):
        """Add an alias and save config."""

        tid = re.match(r'(.)#(\d+)', ptr)

        if not tid:
            raise ValueError("VaultID must be in the format: (.)#(\d+)")

        # Set the alias value
        self.cfg.set('Aliases', alias, ptr)
        
        # Save config.
        self.config_write()

    def alias_del(self, alias):
        """Remove an alias from the config.

        Return True if removed, False otherwise."""

        if self.cfg.has_option('Aliases', alias):
            self.cfg.remove_option('Aliases', alias)
            self.config_write()
            return True
        else:
            return False

    def alias_list(self):
        """Return a list of aliases"""
        return self.cfg.items('Aliases')

    def alias_get(self, alias):
        """Return the pointer for a given alias"""
        if not self.cfg.has_option('Aliases', alias):
            return None
        else:
            return self.cfg.get('Aliases', alias)


    def vaultId(self, vid, prefix, check_alias=True):
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
            tmp = int(vid)
            return tmp
        except:
            pass

        # Match the m#123 formats..
        tid = re.match(r'(.)#(\d+)', vid)
        if tid:
            if tid.group(1) != prefix:
                raise VaultIDFormatError("Bad prefix for VaultID, context requires '%s': %s" % (prefix, vid))
            return int(tid.group(2))

        if check_alias:
            nid = self.alias_get(vid)

            return self.vaultId(nid, prefix, False)

        raise VaultIDFormatError("Invalid alias of bad VaultID format: %s" % vid)



    ### REMOTE ACCESS METHODS


    @authenticate()
    def add_user(self, username, admin=False):
        # TODO: add support for --admin, to give admin privileges

        retval = vaultReply(self.vault.adduser(self.authtok, username, admin),
                            "Error adding user")

        print "Success: %s" % retval['message']
        print "New user ID: u#%d" % retval['user_id']


    @authenticate()
    def del_user(self, username):
        retval = vaultReply(self.vault.deluser(self.authtok, username),
                            "Error removing user")

        print "Success: %s" % retval['message']


    @authenticate()
    def add_customer(self, customer_name):
        retval = vaultReply(self.vault.addcustomer(self.authtok, customer_name),
                            "Error adding customer")

        print "Success: %s" % retval['message']
        print "New customer ID: c#%d" % retval['customer_id']


    @authenticate()
    def add_machine(self, customer_id, name, fqdn, ip, location, notes):
        """Add a machine to the database."""
        # customer_id REQUIRED
        retval = vaultReply(self.vault.addmachine(self.authtok, int(customer_id),
                                                 name or '', fqdn or '', ip or '',
                                                 location or '', notes or ''),
                            "Error adding machine")
        print "Success: %s" % retval['message']
        print "New machine ID: m#%d" % retval['machine_id']


    @authenticate()
    def add_service(self, machine_id, parent_service_id, url, level, secret, notes):
        """Add a service to the Vault's database.

        machine_id - A m#id machine identifier. Specify either machine_id or
                    parent_service_id. 
        parent_service_id - A s#id, parent service ID, to which you should
                            connect before connecting to the service you're
                            adding. Specify 0 of None if no parent exist.
                            If you set this, machine_id is disregarded.
        url - URL of the service, with username, port and path if non-standard.
        level - Security level (or group) of the service. Hopefully an existing
                group level, otherwise, it creates the group.
        notes - Simple text field, with notes.
        secret - Password for the service. Plain-text.
        """

        retval = vaultReply(self.vault.addservice(self.authtok, int(machine_id), int(parent_service_id), url, level, secret, notes or ''),
                            "Error adding service")

        print "Success: %s" % retval['message']
        print "New service ID: s#%d" % retval['service_id']


    @authenticate()
    def grant(self, user, levels):
        """Add permissions to a certain user for a certain level groups.

        user   - a required username.
        levels - array of strings of level labels."""
        #levels = [x.strip() for x in levelstr.split(',')]
        retval = vaultReply(self.vault.grant(self.authtok, user, levels),
                            "Error granting level permissions.")

        
        print "Success: %s" % retval['message']

    
    def setup(self, username, vault_url):
        """Sets up the local configuration to communicate with the Vault.

        username  - the name with which an admin prepared (with add-user)
                    your account.
        vault_url - the URL pointing to the XML-RPC interface of the vault
                    (typically host://domain.example.org:5000/vault/rpc
        """
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
        retval = vaultReply(self.vault.setup(username, serial_elgamal_pubkey(pubkey)),
                            "Setup failed")

        # If Vault sends a SUCCESS, save all the stuff (username, vault_url)
        # and encrypt privkey locally (with Blowfish)
        print "Vault says: %s" % retval['message']

        # Save all (username, vault_url)
        # Encrypt privkey locally (with Blowfish)
        self.cfg.set('SFLvault', 'username', username)
        self._set_vault(vault_url, True)
        # p and x form the private key, add the public key, add g and y.
        # if encryption is required at some point.
        self.cfg.set('SFLvault', 'key', encrypt_privkey(serial_elgamal_privkey([eg.p, eg.x, eg.g, eg.y]), privpass))
        privpass = randfunc(32)
        eg.p = randfunc(32)
        eg.x = randfunc(32)
        del(eg)
        del(privpass)

        print "Saving settings..."
        self.config_write()


    @authenticate()
    def search(self, query, verbose=False):
        """Search the database for query terms, specified as a list of REGEXPs.

        Returns a hierarchical view of the results."""
        retval = vaultReply(self.vault.search(self.authtok, query),
                            "Error searching database")

        print "Results:"
        # TODO: format the results in a beautiful way
        # TODO: call the pager `less` when too long.
        #pprint(retval['results'])
        level = 0
        for c_id, c in retval['results'].items():
            level = 0
            # TODO: display customer info
            print "c#%s  %s" % (c_id, c['name'])

            spc1 = ' ' * (4 + len(c_id))
            for m_id, m in c['machines'].items():
                level = 1
                # TODO: display machine infos: 
                add = ' ' * (4 + len(m_id))
                print "%sm#%s  %s (%s - %s)" % (spc1, m_id,
                                                m['name'], m['fqdn'], m['ip'])
                if verbose:
                    print "%s%slocation: %s" % (spc1, add, m['location'])
                    print "%s%snotes: %s" % (spc1, add, m['notes'])
                                                             

                spc2 = spc1 + add
                for s_id, s in m['services'].items():
                    level = 2
                    # TODO: display service infos
                    add = ' ' * (4 + len(s_id))
                    p_id = s.get('parent_service_id')
                    print "%ss#%s  %s%s" % (spc2, s_id, s['url'],
                                            ("   (depends: s#%s)" % p_id if p_id else ''))
                    if verbose:
                        print "%s%snotes: %s" % (spc2, add, s['notes'])

                if level == 2:
                    print "%s" % (spc2) + '-' * (80 - len(spc2))
                
            if level in [0,1]:
                print "%s" % (spc1) + '-' * (80 - len(spc1))
            


    @authenticate(True)
    def show(self, vid, verbose=False):
        """Show informations to connect to a particular service"""

        retval = vaultReply(self.vault.show(self.authtok, vid),
                            "Error fetching 'show' info.")
        
        print "Results:"

        # TODO: call pager `less` when too long.
        servs = retval['services']
        pre = ''
        for x in retval['services']:
            # Show separator
            if pre:
                pass
                print "%s%s" % (pre, '-' * (80-len(pre)))
                
            spc = len(str(x['id'])) * ' '

            # Decrypt secret
            aeskey = ''
            secret = ''
            if x['usercipher']:
                try:
                    aeskey = self.privkey.decrypt(unserial_elgamal_msg(x['usercipher']))
                except:
                    raise PermissionError("Unable to decrypt Usercipher.")
            
                secret = decrypt_secret(aeskey, x['secret'])
            
            print "%ss#%d %s" % (pre, x['id'], x['url'])
            print "%s%s   secret: %s" % (pre,spc, secret or '[access denied]')
            if verbose:
                print "%s%s   notes: %s" % (pre,spc, x['notes'])
            del(secret)
            del(aeskey)

            pre = pre + '   ' + spc

        # Clean the cache with the private key.
        del(self.privkey)



    @authenticate(True)
    def connect(self, vid):
        """Connect to a distant machine (using SSH for now)"""

        retval = vaultReply(self.vault.show(self.authtok, vid),
                            "Error fetching 'show' info for 'connect()' call.")

        # Check and decrypt all ciphers prior to start connection,
        # if there are some missing, it's not useful to start.
        servs = retval['services']
        for x in retval['services']:
            # Decrypt secret
            aeskey = ''
            secret = ''

            if not x['usercipher']:
                raise RemotingException("We don't have access to password for service %s" % x['url'])
                del(self.privkey) # Clean the cache with the private key.
                break

            try:
                aeskey = self.privkey.decrypt(unserial_elgamal_msg(x['usercipher']))
            except:
                raise PermissionError("Unable to decrypt Usercipher.")

            x['plaintext'] = decrypt_secret(aeskey, x['secret'])

        del(self.privkey) # Clean the cache with the private key.

        connection = remoting.Chain(servs)
        connection.setup()
        connection.connect()

    @authenticate()
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

    @authenticate()
    def list_levels(self):
        """Simply list the available levels"""
        retval = vaultReply(self.vault.listlevels(self.authtok),
                            "Error listing levels")

        print "Levels:"

        for x in retval['list']:
            print "\t%s" % x


    @authenticate()
    def list_machines(self, verbose=False):
        retval = vaultReply(self.vault.listmachines(self.authtok),
                            "Error listing machines")

        print "Machines list:"

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


    @authenticate()
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
        self.vault = (vault or SFLvaultClient())

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
        """Add a user to the Vault."""
        self.parser.set_usage("add-user [options] username")
        self.parser.add_option('-a', '--admin', dest="is_admin",
                               action="store_true", default=False,
                               help="Give admin privileges to the added user")

        self._parse()

        if (len(self.args) != 1):
            raise SFLvaultParserError("Invalid number of arguments")
        
        username = self.args[0]
        admin = self.opts.is_admin

        self.vault.add_user(username, admin)

    def grant(self):
        """Grant level permissions to user.

        Admin privileges required. Use list-levels to have a list."""
        self.parser.set_usage('grant username [options]')
        self.parser.add_option('-l', '--level', dest="levels",
                               action="append", type="string",
                               help="Level to grant to user")
        self._parse()

        if (len(self.args) != 1):
            raise SFLvaultParserError("Invalid number of arguments, 'username' required.")

        username = self.args[0]
        levels = self.opts.levels

        retval = self.vault.grant(username, levels)
        # TODO: We'll receive all the pubkeys over here, and we need to re-
        # encode all the symkeys for passwords on that level.

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


    def add_machine(self):
        """Add a machine to the Vault's database."""
        self.parser.set_usage("add-machine [options]")
        self.parser.add_option('-c', '--customer', dest="customer_id",
                               help="Customer id, as 'c#123' or '123'")
        self.parser.add_option('-n', '--name', dest="name",
                               help="Machine name, used for display everywhere")
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
        customer_id = self.vault.vaultId(o.customer_id, 'c')
        self.vault.add_machine(customer_id, o.name, o.fqdn,
                              o.ip, o.location, o.notes)


    def add_service(self):
        """Add a service to a particular machine in the Vault's database.

        The secret/password/authentication key will be asked in the
        interactive prompt.

        Note : Passwords will never be taken from the URL when invoked on the
               command-line, to prevent sensitive information being held in
               history.
        """
        
        self.parser.add_option('-m', '--machine', dest="machine_id",
                               help="Service will be attached to machine, as 'm#123' or '123'")
        self.parser.add_option('-u', '--url', dest="url",
                               help="Service URL, full proto://[username@]fqdn.example.org[:port][/path[#fragment]], WITHOUT the secret.")

        self.parser.add_option('-s', '--parent', dest="parent_id",
                               help="Parent's Service ID for this new one.")
        self.parser.add_option('-v', '--level', dest="level", default='',
                               help="Access level (access group) for this service. Use list-levels to get a complete list of access levels.")
        self.parser.add_option('--notes', dest="notes",
                               help="Notes about the service, references, URLs.")

        self._parse()

        if not self.opts.url:
            raise SFLvaultParserError("Required parameter 'url' omitted")
        
        ## TODO: make a list-customers and provide a selection using arrows or
        #        or something alike.
        if not self.opts.machine_id and not self.opts.parent_id:
            raise SFLvaultParserError("Parent ID or Machine ID required. Please specify -r|--parent VaultID or -m|--machine VaultID")

        o = self.opts

        url = urlparse.urlparse(o.url)

        # TODO: check if we're on the command line (and not in the SFLvault
        #       shell. If we're not in the CLI, then we can take the secret
        #       from the URL, if available. Otherwise, ask.
        secret = None


        # TODO: plug-in-ize password capture.
        if not secret:
            secret = getpass.getpass("Enter service secret (password): ")

        # TODO: rewrite url if a password was included... strip the port and
        #       username from the URL too.

        machine_id = 0
        parent_id = 0
        if o.machine_id:
            machine_id = self.vault.vaultId(o.machine_id, 'm')
        if o.parent_id:
            parent_id = self.vault.vaultId(o.parent_id, 's')
            
        self.vault.add_service(machine_id, parent_id, o.url, o.level, secret,
                               o.notes)
        del(secret)


    def alias(self):
        """Set an alias, local shortcut to VaultIDs (s#123, m#87, etc..)

        List, view or set an alias."""
        self.parser.set_usage("alias [options] [alias [VaultID]]")

        self.parser.add_option('-d', '--delete', dest="delete",
                               metavar="ALIAS", help="Delete the given alias")

        self._parse()

        if self.opts.delete:
            
            res = self.vault.alias_del(self.opts.delete)

            if res:
                print "Alias removed"
            else:
                print "No such alias"

        elif len(self.args) == 0:
            
            # List aliases
            l = self.vault.alias_list()
            print "Aliases:"
            for x in l:
                print "\t%s\t%s" % (x[0], x[1])

        elif len(self.args) == 1:

            # Show this alias's value
            a = self.vault.alias_get(self.args[0])
            if a:
                print "Alias:"
                print "\t%s\t%s" % (self.args[0], a)
            else:
                print "Invalid alias"

        elif len(self.args) == 2:
            try:
                r = self.vault.alias_add(self.args[0], self.args[1])
            except ValueError, e:
                raise SFLvaultParserError(e.message)

            print "Alias added"

        else:
            raise SFLvaultParserError("Invalid number of parameters")


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

    def list_levels(self):
        """List existing levels."""
        self._parse()

        if len(self.args):
            raise SFLvaultParserError("Invalid number of arguments")

        self.vault.list_levels()


    def list_machines(self):
        """List existing machines.

        This command will list all machines in the Vault's database."""
        ## TODO: add support for listing only machines of a certain c#id
        #        (customer_id)
        self.parser.add_option('-v', '--verbose', action="store_true",
                               dest='verbose', default=False,
                               help="Enable verbose output (location and notes)")
        self._parse()

        if len(self.args):
            raise SFLvaultParserError("Invalid number of arguments")

        self.vault.list_machines(self.opts.verbose)
        

    def setup(self):
        """Setup a new user on the vault.

        Call this after an admin has called `add-user` on the Vault.
        
        username  - the username used in the `add-user` call.
        vault_url - the URL (http://example.org:port/vault/rpc) to the
                    Vault"""
        
        self.parser.set_usage("setup username vault_url")
        self._parse()
        
        if len(self.args) != 2:
            raise SFLvaultParserError("Invalid number of arguments")

        username = self.args[0]
        url      = self.args[1]

        self.vault.setup(username, url)

    def show(self):
        """Show informations to connect to a particular service.

        VaultID - service ID as 's#123', '123', or alias pointing to a service
                  ID."""
        self.parser.set_usage("show [opts] VaultID")
        self.parser.add_option('-v', '--verbose', dest="verbose",
                               help="Show verbose output (include notes, location)")
        self._parse()

        if len(self.args) != 1:
            raise SFLvaultParserError("Invalid number of arguments")

        vid = self.vault.vaultId(self.args[0], 's')
        verbose = self.opts.verbose

        self.vault.show(vid, verbose)




    def connect(self):
        """Connect to a remote SSH host, sending password on the way.

        VaultID - service ID as 's#123', '123', or alias pointing to a service
                  ID."""
        self.parser.set_usage("connect VaultID")
        self.parser.add_option('-v', '--verbose', dest="verbose",
                               help="Verbose (unused, only for compat. with 'show')")
        self._parse()

        if len(self.args) != 1:
            raise SFLvaultParserError("Invalid number of arguments")

        vid = self.vault.vaultId(self.args[0], 's')

        self.vault.connect(vid)



    def search(self):
        """Search the Vault's database for those space separated regexp"""
        self.parser.set_usage('search [opts] regexp1 ["reg exp2" ...]')
        self.parser.add_option('-v', '--verbose', dest="verbose",
                               action="store_true", default=False,
                               help="Show verbose output (include notes, location)")
        self._parse()

        if not len(self.args):
            raise SFLvaultParserError("Search terms required")

        self.vault.search(self.args, self.opts.verbose)






###
### Execute requested command-line command
###    
def main():
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
        print "[SFLvault] XML-RPC Fault: %s" % e.faultString
    except VaultConfigurationError, e:
        print "[SFLvault] Configuration error: %s" % e
    except RemotingError, e:
        print "[SFLvault] Remoting error: %s" % e.message
    except ServiceRequireError, e:
        print "[SFLvault] Service-chain setup error: %s" % e.message
    except DecryptError, e:
        print "[SFLvault] There has been an error in decrypting messages: %s" \
              % e.message

    

# For wrappers.
if __name__ == "__main__":

    main()
