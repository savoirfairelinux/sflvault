# -=- encoding: utf-8 -=-
#
# SFLvault - Secure networked password store and credentials manager.
#
# Copyright (C) 2008-2009  Savoir-faire Linux inc.
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

import pkg_resources as pkgres
from ConfigParser import ConfigParser, NoSectionError
import xmlrpclib
import getpass
import sys
import re
import os

from subprocess import Popen, PIPE

from decorator import decorator
from pprint import pprint

from sflvault.common import VaultError
from sflvault.common.crypto import *
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
        privkey = None

        # Check if we've cached the decrypted private key
        if hasattr(self, 'privkey'):
            # Use cached private key.
            privkey = self.privkey

        else:

            try:
                privkey_enc = self.cfg.get('SFLvault', 'key')
            except:
                raise VaultConfigurationError("No private key in local config, init with: user-setup username vault-url")
        
            try:
                privpass = self.getpassfunc()
                privkey_packed = decrypt_privkey(privkey_enc, privpass)
                del(privpass)
                eg = ElGamal.ElGamalobj()
                (eg.p, eg.x, eg.g, eg.y) = unserial_elgamal_privkey(privkey_packed)
                privkey = eg

            except DecryptError, e:
                print "[SFLvault] Invalid passphrase"
                return False
            except KeyboardInterrupt, e:
                print "[aborted]"
                return False

            # When we ask to keep the privkey, keep the ElGamal obj.
            if keep_privkey or self.shell_mode:
                self.privkey = privkey


        # Go for the login/authenticate roundtrip

        # TODO: check also is the privkey (ElGamal obj) has been cached
        #       in self.privkey (when invoked with keep_privkey)
        retval = self.vault.login(username, pkgres.get_distribution('SFLvault_client').version)
        self.authret = retval
        if not retval['error']:
            # decrypt token.

            cryptok = privkey.decrypt(unserial_elgamal_msg(retval['cryptok']))
            retval2 = self.vault.authenticate(username, b64encode(cryptok))
            self.authret = retval2
        
            if retval2['error']:
                raise AuthenticationError("Authentication failed: %s" % \
                                          retval2['message'])
            else:
                self.authtok = retval2['authtok']
                print "Authentication successful"
        else:
            raise AuthenticationError("Authentication failed: %s" % \
                                      retval['message'])

        return func(self, *args, **kwargs)

    return decorator(do_authenticate)

###
### Différentes façons d'obtenir la passphrase
###
class AskPassMethods(object):
    """Wrapper for askpass methods"""
    
    env_var = 'SFLVAULT_ASKPASS'

    def program(self):
        try:
            p = Popen(args=[self._program_value], shell=False, stdout=PIPE)
            p.wait()
            return p.stdout.read()
        except OSError, e:
            msg = "Failed to run '%s' : %s" % (os.environ[self.env_var], e)
            raise ValueError(msg)

    def default(self):
        """Default function to get passphrase from user, for authentication."""
        return getpass.getpass("Vault passphrase: ", stream=sys.stderr)
    
    def __init__(self, config):
        # Default
        self.getpass = self.default
        self.cfg = config

        # Use 'program' is SFLVAULT_ASKPASS env var exists
        env_var = AskPassMethods.env_var
        if env_var in os.environ:
            self._program_value = os.environ[env_var]
            self.getpass = self.program
            return

        wallet_name = self.cfg.wallet_get()

        def keyring_wallet():
            self.cfg._check_keyring()
            import keyring
            backend = self.cfg.wallet_get_obj()
            return backend.get_password("sflvault", self.cfg._wallet_key)

        if wallet_name:
            self.getpass = keyring_wallet

###
### Configuration manager for SFLvault
###
class SFLvaultConfig(object):
    """This object deals with everything configuration.

    It handles the aliases adding/removal and talks with other systems
    through Exceptions.

    It handles the keyring support and passwords management

    """
    def __init__(self, config_file):
        self.config_file = os.path.expanduser(config_file)
        self.config_check()
        self.config_read()
        
        
    def config_check(self):
        """Checks for ownership and modes for all paths and files, à-la SSH"""
        fullfile = self.config_file
        fullpath = os.path.dirname(self.config_file)
    
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
        self.cfg = ConfigParser()
        fp = open(self.config_file, 'r')
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
        fp = open(self.config_file, 'w')
        self.cfg.write(fp)
        fp.close()

    # Fake being the actual ConfigParser object
    def get(self, *args, **kwargs):
        return self.cfg.get(*args, **kwargs)
    def set(self, *args, **kwargs):
        return self.cfg.set(*args, **kwargs)
    def has_option(self, *args, **kwargs):
        return self.cfg.has_option(*args, **kwargs)

    def alias_add(self, alias, ptr):
        """Add an alias and save config."""
        tid = re.match(r'(.)#(\d+)', ptr)
        if not tid:
            raise ValueError("VaultID must be in the format: (.)#(\d+)")

        # Set the alias value
        self.cfg.set('Aliases', alias, ptr)
        # Save config.
        self.config_write()
        return True

    def alias_del(self, alias):
        """Remove an alias from the config.

        :rtype: True if removed, False otherwise.
        """
        if self.cfg.has_option('Aliases', alias):
            self.cfg.remove_option('Aliases', alias)
            self.config_write()
            return True
        else:
            return False

    def alias_list(self):
        """Return a list of aliases

        :rtype: list of (alias, value) pairs.
        """
        return self.cfg.items('Aliases')

    def alias_get(self, alias):
        """Return the pointer for a given alias"""
        if not self.cfg.has_option('Aliases', alias):
            return None
        else:
            return self.cfg.get('Aliases', alias)


    def _check_keyring(self):
        try:
            import keyring
        except ImportError, e:
            raise KeyringError("No keyring support, please install python-keyring")
        
    def wallet_list(self):
        """Return the list of available wallets, from Keyring

        [('0', 'Manual', None, 'Disabled', True),
         ('1', 'UncryptedKeyring', <UncryptedKeyring object>, 'Recommended', False),
         ...]
        """
        self._check_keyring()
        import keyring

        current = self.wallet_get()
        out = [('0', 'Manual', None, 'Disabled', current == None)]
        ref = {1: "Recommended", 0: "Supported", -1: "Not installed"} 
        for i, backend in enumerate(keyring.backend.get_all_keyring()):
            out.append((str(i + 1),
                        backend.__class__.__name__,
                        backend,
                        ref[backend.supported()],
                        backend.__class__.__name__ == current,
                        ))
        return out
        
    @property
    def _wallet_key(self):
        """Standardizes the key to be stored in the keystore"""
        return re.subn(r'\.+', '.', re.subn(r'[-_:\\ /]', '.',
                                               self.config_file)[0].lower())[0]

    def wallet_set(self, id, password):
        if id is None or id == '0':
            self.cfg.remove_option('SFLvault', 'wallet')
        else:
            lst = self.wallet_list()
            ids = [x[0] for x in lst]
            if id not in ids:
                raise KeyringError("No such Wallet ID: %s" % id)
            backend = [x for x in lst if x[0] == id][0]
            ret = backend[2].set_password("sflvault", self._wallet_key,
                                          password)
            if ret:  # Error saving the password ?
                raise KeyringError("Unable to store password in keyring")
            # Set the wallet value
            self.cfg.set('SFLvault', "wallet", backend[1])
        # Save config.
        self.config_write()
        return True

    def wallet_get(self):
        """Return the currently configured wallet, otherwise None"""
        if self.cfg.has_option('SFLvault', 'wallet'):
            return self.cfg.get('SFLvault', 'wallet')
        else:
            return None

    def wallet_get_obj(self):
        """Return the currently configured wallet as a backend object,
        otherwise None
        """
        name = self.wallet_get()
        if not name:
            return None

        lst = self.wallet_list()
        names = [x[1] for x in lst]
        if name not in names:
            raise KeyringError("No such Wallet type: %s" % name)
        self.wallet_test(name)

        backend = [x[2] for x in lst if x[1] == name][0]
        return backend

    def wallet_test(self, name):
        """Test if the Wallet is supported, otherwise, suggest to install
        packages
        """
        lst = self.wallet_list()
        backend = [x[2] for x in lst if x[1] == name][0]
        assoc = {'CryptedFileKeyring': 'python-keyring',
                 'UncryptedFileKeyring': 'python-keyring',
                 'KDEKWallet': 'python-keyring-kwallet',
                 'GnomeKeyring': 'python-keyring-gnome',
                 }
        if backend.supported() == -1:
            if name in assoc:
                add = ' To add support, please install the `%s` package.' % \
                    assoc[name]
            raise KeyringError("Keyring (%s) is not supported.%s "
                               "Use the `wallet` command to reconfigure." %
                               (name, add))
        return True

###
### On définit les fonctions qui vont traiter chaque sorte de requête.
###
class SFLvaultClient(object):
    """This is the main SFLvault Client object.

    It is used to script some access to the vault, to retrieve data, to store
    data, or to create a GUI interface on the top of it.

    Whether you want to access a local or remote Vault server, this is the
    object you need.
    """
    def __init__(self, config, shell=False):
        """Set up initial configuration for function calls

        :param config: Configuration filename to use.
        :param shell: if True, the private key will be cached for a while,
            not asking your password for each query to the vault.
        """
        # Load configuration
        self.cfg = SFLvaultConfig(config)

        # The function to call upon @authenticate to get passphrase from user.
        self.set_getpassfunc(None)

        self.shell_mode = shell
        self.authtok = ''
        self.authret = None
        # Set the default route to the Vault
        url = self.cfg.get('SFLvault', 'url')
        if url:
            self.vault = xmlrpclib.Server(url, allow_none=True).sflvault

    def set_getpassfunc(self, func=None):
        """Set the function to ask for passphrase.

        By default, it is set to _getpass, which asks for the passphrase on the
        command line, but you can create a new function, that would for example
        pop-up a window, or use another mechanism to ask for passphrase and
        continue authentication."""
        if not func:
            self.getpassfunc = AskPassMethods(self.cfg).getpass
        else:
            self.getpassfunc = func
        
    def _set_vault(self, url, save=False):
        """Set the vault's URL and optionally save it"""
        self.vault = xmlrpclib.Server(url, allow_none=True).sflvault
        if save:
            self.cfg.set('SFLvault', 'url', url)

    def vaultId(self, vid, prefix, check_alias=True):
        """Return an integer value for a given VaultID.
        
        A VaultID can be one of the following:
        
        * ``123`` - treated as is, and assumed to be of type `prefix`.
        * ``m#123`` - checked against `prefix`, otherwise raises an exception.
        * ``alias`` - checked against `prefix` and the aliases that are in
          the configuration, returns an integer, or raises an exception.

        :param check_alias: check for matching aliases if True, otherwise only
          the two first cases are treated.
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
                raise VaultIDSpecError("Bad prefix for VaultID, "\
                                         "context requires '%s': %s"\
                                         % (prefix, vid))
            return int(tid.group(2))

        if check_alias:
            nid = self.cfg.alias_get(vid)

            if not nid:
                raise VaultIDSpecError("No such alias '%s'. Use `alias %s %s#[ID]` to set." % (vid, vid, prefix))

            return self.vaultId(nid, prefix, False)

        raise VaultIDSpecError("Invalid VaultID format: %s" % vid)



    ### REMOTE ACCESS METHODS


    @authenticate()
    def user_add(self, username, admin=False):
        # TODO: add support for --admin, to give admin privileges

        retval = vaultReply(self.vault.user_add(self.authtok, username, admin),
                            "Error adding user")

        print "Success: %s" % retval['message']
        prms = (username, self.cfg.get('SFLvault', 'url'))
        print "The new user should run: sflvault user-setup %s %s" % prms

        return retval


    @authenticate()
    def user_del(self, username):
        retval = vaultReply(self.vault.user_del(self.authtok, username),
                            "Error removing user")

        print "Success: %s" % retval['message']

        return retval


    def _services_returned(self, retval):
        """Helper function for customer_del, machine_del and service_del."""
        
        if retval['error']:
            print "Error: %s" % retval['message']

            if 'childs' in retval:
                print "Those services rely on services you were going "\
                      "to delete:"
                for x in retval['childs']:
                    print "     s#%s%s%s" % (x['id'],
                                             ' ' * (6 - len(str(x['id']))),
                                             x['url'])
        else:
            print "Success: %s" % retval['message']


    @authenticate()
    def customer_del(self, customer_id):
        retval = self.vault.customer_del(self.authtok, customer_id)

        self._services_returned(retval)

        return retval
        

    @authenticate()
    def machine_del(self, machine_id):
        retval = self.vault.machine_del(self.authtok, machine_id)

        self._services_returned(retval)
        
        return retval


    @authenticate(True)
    def customer_get(self, customer_id):
        """Get information to be edited"""
        retval = vaultReply(self.vault.customer_get(self.authtok, customer_id),
                            "Error fetching data for customer %s" % customer_id)

        return retval['customer']

    @authenticate(True)
    def customer_put(self, customer_id, data):
        """Save the (potentially modified) customer to the Vault"""
        retval = vaultReply(self.vault.customer_put(self.authtok, customer_id,
                                                   data),
                            "Error saving data to vault, aborting.")

        print "Success: %s " % retval['message']

        return retval
        

    @authenticate()
    def service_del(self, service_id):
        retval = self.vault.service_del(self.authtok, service_id)

        self._services_returned(retval)

        return retval


    @authenticate()
    def customer_add(self, customer_name):
        retval = vaultReply(self.vault.customer_add(self.authtok,
                                                    customer_name),
                            "Error adding customer")

        print "Success: %s" % retval['message']
        print "New customer ID: c#%d" % retval['customer_id']

        return retval


    @authenticate()
    def machine_add(self, customer_id, name, fqdn, ip, location, notes):
        """Add a machine to the database."""
        # customer_id REQUIRED
        retval = vaultReply(self.vault.machine_add(self.authtok,
                                                   int(customer_id),
                                                   name or '', fqdn or '',
                                                   ip or '', location or '',
                                                   notes or ''),
                            "Error adding machine")
        print "Success: %s" % retval['message']
        print "New machine ID: m#%d" % int(retval['machine_id'])

        return retval

    @authenticate()
    def service_add(self, machine_id, parent_service_id, url, group_ids, secret,
                    notes, metadata=None):
        """Add a service to the Vault's database.

        machine_id - A m#id machine identifier.
        parent_service_id - A s#id, parent service ID, to which you should
                            connect before connecting to the service you're
                            adding. Specify 0 or None if no parent exist.
                            If you set this, machine_id is disregarded.
        url - URL of the service, with username, port and path if required
        group_ids - Multiple group IDs the service is part of. See `list-groups`
        notes - Simple text field, with notes.
        secret - Password for the service. Plain-text.
        metadata - Dictionary with metadata for services (depends on service).
        """

        # TODO: accept group_id as group_ids, accept list and send list.
        psi = int(parent_service_id) if parent_service_id else None
        retval = vaultReply(self.vault.service_add(self.authtok,
                                                  int(machine_id),
                                                  psi, url,
                                                  group_ids, secret,
                                                  notes or '',
                                                  metadata),
                            "Error adding service")

        print "Success: %s" % retval['message']
        print "New service ID: s#%d" % retval['service_id']

        return retval

    @authenticate()
    def service_passwd(self, service_id, newsecret):
        """Updates the password on the Vault for a certain service"""
        retval = vaultReply(self.vault.service_passwd(self.authtok,
                                                        service_id,
                                                        newsecret),
                            "Error changing password for "\
                            "service %s" % service_id)

        print "Success: %s" % retval['message']
        print "Password updated for service: s#%d" % int(retval['service_id'])

        return retval
                            

    def _new_passphrase(self):
        """Return a new passphrase after asking arrogantly"""
        while True:
            passphrase = getpass.getpass("Enter passphrase (to secure "
                                         "your private key): ")
            passph2 = getpass.getpass("Enter passphrase again: ")

            if passphrase != passph2:
                print "Passphrase mismatch, try again."
            elif passphrase == '':
                print "Passphrase cannot be null."
            else:
                return passphrase

    def user_passwd(self, new_passphrase=None):
        """Change the password protecting the local private key."""
        old_passphrase = getpass.getpass('Enter your old passphrase: ')
        # Re-read configuration in case it changed since the shell is open.
        self.cfg.config_read()
        privkey_enc = self.cfg.get('SFLvault', 'key')
        # Decrypt the privkey
        try:
            thething = decrypt_privkey(privkey_enc, old_passphrase)
        except DecryptError, e:
            print "[SFLvault] Invalid passphrase"
            return
        del(privkey_enc)
        # Ask the new passphrase, 
        if not new_passphrase:
            new_passphrase = self._new_passphrase()
        # Encrypt and set the new passphrase
        self.cfg.set('SFLvault', 'key', encrypt_privkey(thething, new_passphrase))
        self.cfg.config_write()

        print "user-passwd successful"
        
    def user_setup(self, username, vault_url, passphrase=None):
        """Sets up the local configuration to communicate with the Vault.

        username  - the name with which an admin prepared (with add-user)
                    your account.
        vault_url - the URL pointing to the XML-RPC interface of the vault
                    (typically host://domain.example.org:5000/vault/rpc
        passphrase - use the given passphrase instead of asking it on the
                     command line.
        """
        # possible-TODO: implement --force if user wants to override.
        if self.cfg.has_option('SFLvault', 'key'):
            raise VaultConfigurationError("WARNING: you already have a private key stored in %s.  Backup/rename this file before running this command again." % (self.cfg.config_file))
            
        self._set_vault(vault_url, False)
        
        # Generate a new key:
        print "Generating new ElGamal key-pair..."
        eg = generate_elgamal_keypair()

        # Marshal the ElGamal key
        pubkey = elgamal_pubkey(eg)

        print "You will need a passphrase to secure your private key. The"
        print "encrypted key will be stored on this machine in %s" % self.cfg.config_file
        print '-' * 80

        if not passphrase:
            passphrase = self._new_passphrase()
        
        print "Sending request to vault..."
        # Send it to the vault, with username
        retval = vaultReply(self.vault.user_setup(username,
                                                serial_elgamal_pubkey(pubkey)),
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
        self.cfg.set('SFLvault', 'key',
                   encrypt_privkey(serial_elgamal_privkey(elgamal_bothkeys(eg)),
                                   passphrase))
        del(passphrase)
        del(eg)

        print "Saving settings..."
        self.cfg.config_write()


    @authenticate()
    def search(self, query, filters=None, verbose=True):
        """Search the database for query terms.

        query - list of REGEXPs to be matched
        filters - is a dict with keys in ['groups', 'machines', 'customers']
                  that limits the records returned to those matching those
                  constraints. The values can be either int or str
                  (representing an int).
        verbose - shows the notes and location attributes for services
                  and machines.

        Returns a hierarchical view of the results.
        """

        # Remove empty filters:
        if filters:
            filters = dict([(x, filters[x]) for x in filters if filters[x]])

        retval = vaultReply(self.vault.search(self.authtok, query,
                 filters.get('groups') if filters else None, verbose, filters),
                            "Error searching database")
        print "Results:"
        encode = lambda x: x.encode('utf-8') if isinstance(x, unicode) else x

        # TODO: call the pager `less` when too long.
        level = 0
        for c_id, c in retval['results'].items():
            level = 0
            # Display customer info
            print "c#%s  %s" % (c_id, encode(c['name']))

            spc1 = ' ' * (4 + len(c_id))
            for m_id, m in c['machines'].items():
                level = 1
                # Display machine infos: 
                add = ' ' * (4 + len(m_id))
                print "%sm#%s  %s (%s - %s)" % (spc1, m_id,
                                                encode(m['name']),
                                                m['fqdn'], m['ip'])
                if verbose:
                    if m['location']:
                        print "%s%slocation: %s" % (spc1, add,
                                                 encode(m['location']))
                    if m['notes']:
                        print "%s%snotes: %s" % (spc1, add,
                                                 encode(m['notes']))

                spc2 = spc1 + add
                print ""
                for s_id, s in m['services'].items():
                    level = 2
                    # Display service infos
                    add = ' ' * (4 + len(s_id))
                    p_id = s.get('parent_service_id')
                    print "%ss#%s  %s%s" % (spc2, s_id,
                                            encode(s['url']),
                                            ("   (depends: s#%s)" % \
                                             p_id if p_id else ''))
                    if verbose:
                        if s['notes']:
                            print "%s%snotes: %s" % (spc2, add,
                                                     encode(s['notes']))

                if level == 2:
                    print "%s" % (spc2) + '-' * (80 - len(spc2))
                
            if level in [0,1]:
                print "%s" % (spc1) + '-' * (80 - len(spc1))

        return retval
            
    def _decrypt_service(self, serv, onlysymkey=False, onlygroupkey=False):
        """Decrypt the service object returned from the vault.

        onlysymkey - return the plain symkey in the result
        onlygroupkey - return the plain groupkey ElGamal obj in result
        """
        # First decrypt groupkey
        try:
            # TODO: implement a groupkey cache system, since it's the longest
            #       thing to decrypt (over a second on a 3GHz machine)
            grouppacked = decrypt_longmsg(self.privkey, serv['cryptgroupkey'])
        except Exception, e:
            raise DecryptError("Unable to decrypt groupkey (%s)" % e)

        eg = ElGamal.ElGamalobj()
        (eg.p, eg.x, eg.g, eg.y) = unserial_elgamal_privkey(grouppacked)
        groupkey = eg
        
        if onlygroupkey:
            serv['groupkey'] = eg
            
        # Then decrypt symkey
        try:
            aeskey = decrypt_longmsg(groupkey, serv['cryptsymkey'])
        except Exception, e:
            raise DecryptError("Unable to decrypt symkey (%s)" % e)

        if onlysymkey:
            serv['symkey'] = aeskey

        if not onlygroupkey and not onlysymkey:
            serv['plaintext'] = decrypt_secret(aeskey, serv['secret'])


    @authenticate(True)
    def service_get(self, service_id, decrypt=True):
        """Get information to be edited"""
        retval = vaultReply(self.vault.service_get(self.authtok, service_id),
                            "Error fetching data for service %s" % service_id)

        serv = retval['service']
        # Decrypt secret
        aeskey = ''
        secret = ''

        if decrypt:
            # Add it only if we can! (or if we want to)
            if serv.get('cryptgroupkey'):
                self._decrypt_service(serv)

        return serv


    @authenticate(True)
    def service_get_tree(self, service_id, with_groups=False):
        """Get information to be edited"""
        return self._service_get_tree(service_id, with_groups)

    def _service_get_tree(self, service_id, with_groups=False):
        """Same as service_get_tree, but without authentication, so
        that it can be called by ``show`` and ``connect``.
        """
        retval = vaultReply(self.vault.service_get_tree(self.authtok,
                                                        service_id,
                                                        with_groups),
                "Error fetching data-tree for service %s" % service_id)

        for x in retval['services']:
            # Decrypt secret
            aeskey = ''
            secret = ''

            if not x['cryptsymkey']:
                # Don't add a plaintext if we can't.
                continue

            self._decrypt_service(x)

        return retval['services']


    @authenticate(True)
    def service_put(self, service_id, data):
        """Save the (potentially modified) service to the Vault"""
        retval = vaultReply(self.vault.service_put(self.authtok, service_id,
                                                   data),
                            "Error saving data to vault, aborting.")

        print "Success: %s " % retval['message']

        return retval
        

    @authenticate(True)
    def machine_get(self, machine_id):
        """Get information to be edited"""
        retval = vaultReply(self.vault.machine_get(self.authtok, machine_id),
                            "Error fetching data for machine %s" % machine_id)

        return retval['machine']

    @authenticate(True)
    def machine_put(self, machine_id, data):
        """Save the (potentially modified) machine to the Vault"""
        retval = vaultReply(self.vault.machine_put(self.authtok, machine_id,
                                                   data),
                            "Error saving data to vault, aborting.")

        print "Success: %s " % retval['message']
        
        return retval

    @authenticate(True)
    def show(self, service_id, verbose=False, with_groups=False):
        """Show informations to connect to a particular service"""
        servs = self._service_get_tree(service_id, with_groups)
        self._show(servs, verbose)

    def _show(self, services, verbose=False):
        """Show results fetched by _service_get_tree, to be called by both
        `show` and `connect`."""
        print "Results:"
        pre = ''
        for x in services:
            # Show separator
            if pre:
                pass
                #print "%s%s" % (pre, '-' * (80-len(pre)))
                
            spc = len(str(x['id'])) * ' '

            secret = x['plaintext'] if 'plaintext' in x else '[access denied]'
            print "%ss#%d %s" % (pre, x['id'], x['url'])
            if x['groups_list']:
                groups = ', '.join(["g#%s %s" % (g[0], g[1])
                                    for g in x['groups_list']])
                print "%s%s   groups: %s" % (pre, spc, groups)
            print "%s%s   secret: %s" % (pre, spc, secret)
            
            if verbose:
                print "%s%s   notes: %s" % (pre,spc, x['notes'])
                if x['metadata']:
                    print "%s%s   metadata:" % (pre, spc)
                    for key, val in x['metadata'].items():
                        print "%s%s     %s: %s" % (pre, spc, key, val)

            del(secret)

            pre = pre + '   ' + spc


    @authenticate(True)
    def connect(self, vid, with_show=False, command_line=''):
        """Connect to a distant machine (using SSH for now)"""
        servs = self._service_get_tree(vid)

        if with_show:
            self._show(servs)

        # Check and decrypt all ciphers prior to start connection,
        # if there are some missing, it's not useful to start.
        for x in servs:
            if not x['cryptsymkey']:
                raise RemotingError("We don't have access to password for service %s" % x['url'])

        connection = remoting.Chain(servs, command_line=command_line)
        connection.setup()
        connection.connect()
        #connection.debug_chain()

    @authenticate()
    def user_list(self, groups=False):
        """List users

        ``groups`` - if True, list groups for each user also
        """
        # Receive: [{'id': x.id, 'username': x.username,
        #            'created_time': x.created_time,
        #            'is_admin': x.is_admin,
        #            'setup_expired': x.setup_expired()}
        #            {}, {}, ...]
        #    
        retval = vaultReply(self.vault.user_list(self.authtok, groups),
                            "Error listing users")

        print "User list (with creation date):"
        
        to_clean = []  # Expired users to be removed
        for x in retval['list']:
            add = ''
            if x['is_admin']:
                add += ' [global admin]'
            if x['setup_expired']:
                add += ' [setup expired]'
                to_clean.append(x['username'])
            if x['waiting_setup'] and not x['setup_expired']:
                add += ' [in setup process]'

            # TODO: load the xmlrpclib.DateTime object into something more fun
            #       to deal with! Some day..
            print "u#%d\t%s\t%s %s" % (x['id'], x['username'],
                                       x['created_stamp'], add)

            if 'groups' in x:
                for grp in x['groups']:
                    add = ' [admin]' if grp['is_admin'] else ''
                    print "\t\tg#%s\t%s %s" % (grp['id'], grp['name'], add)

        print '-' * 80

        if len(to_clean):
            print "There are expired users. To remove them, run:"
            for usr in to_clean:
                print "   sflvault user-del -u %s" % usr

        return retval
        

    @authenticate(True)
    def group_get(self, group_id):
        """Get information to be edited"""
        retval = vaultReply(self.vault.group_get(self.authtok, group_id),
                            "Error fetching data for group %s" % group_id)

        return retval['group']

    @authenticate(True)
    def group_put(self, group_id, data):
        """Save the (potentially modified) Group to the Vault"""
        retval = vaultReply(self.vault.group_put(self.authtok, group_id,
                                                   data),
                            "Error saving data to vault, aborting.")

        print "Success: %s " % retval['message']
        
        return retval


    @authenticate(True)
    def group_add_service(self, group_id, service_id):
        print "Fetching service info..."
        retval = vaultReply(self.vault.service_get(self.authtok, service_id),
                            "Error loading service infos")

        # TODO: decrypt the symkey with the group's decrypted privkey.
        serv = retval['service']

        print "Decrypting symkey..."
        self._decrypt_service(serv, onlysymkey=True)


        print "Sending data back to vault"
        retval = vaultReply(self.vault.group_add_service(self.authtok,
                                                         group_id,
                                                         service_id,
                                                         serv['symkey']),
                            "Error adding service to group")

        print "Success: %s" % retval['message']

        return retval

    @authenticate()
    def group_del_service(self, group_id, service_id):
        retval = vaultReply(self.vault.group_del_service(self.authtok, group_id,
                                                 service_id),
                            "Error removing service from group")

        print "Success: %s" % retval['message']

        return retval

    @authenticate(True)
    def group_add_user(self, group_id, user, is_admin=False):
        retval = vaultReply(self.vault.group_add_user(self.authtok, group_id,
                                                      user),
                            "Error adding user to group")

        # Decrypt cryptgroupkey
        # TODO: make use of a cache
        grouppacked = decrypt_longmsg(self.privkey, retval['cryptgroupkey'])
        
        # Get userpubkey and unpack
        eg = ElGamal.ElGamalobj()
        (eg.p, eg.g, eg.y) = unserial_elgamal_pubkey(retval['userpubkey'])
        
        # Re-encrypt for user
        newcryptgroupkey = encrypt_longmsg(eg, grouppacked)
        
        # Return a well-formed database-ready cryptgroupkey for user,
        # also, give the param is_admin.. as desired.
        retval = vaultReply(self.vault.group_add_user(self.authtok, group_id,
                                                      user, is_admin,
                                                      newcryptgroupkey),
                            "Error adding user to group")

        print "Success: %s" % retval['message']

        return retval

    @authenticate()
    def group_del_user(self, group_id, user):
        retval = vaultReply(self.vault.group_del_user(self.authtok, group_id,
                                                      user),
                            "Error removing user from group")

        print "Success: %s" % retval['message']
    
    @authenticate()
    def group_add(self, group_name):
        """Add a named group to the Vault. Return the group id."""
        
        print "Please wait, Vault generating keypair..."
        
        retval = vaultReply(self.vault.group_add(self.authtok, group_name),
                            "Error adding group")

        print "Success: %s " % retval['message']
        print "New group id: g#%d" % retval['group_id']

        return retval


    @authenticate()
    def group_del(self, group_id):
        """Remove a group from the Vault, making sure no services are left
        behind."""
        retval = vaultReply(self.vault.group_del(self.authtok, group_id),
                            "Error removing group")

        print "Success: %s" % retval['message']

    @authenticate()
    def group_list(self, quiet=False):
        """Simply list the available groups"""
        retval = vaultReply(self.vault.group_list(self.authtok),
                            "Error listing groups")

        print "Groups:"

        lst = retval['list']
        lst.sort(key=lambda x: x['name'])
        
        show_legend = False
        for grp in lst:
            add = []
            if grp.get('hidden', False):
                add.append('[hidden]')
            if grp.get('member', False):
                add.append('[member]')
            if grp.get('admin', False):
                add.append('[admin]')
            print "\tg#%d\t%s %s" % (grp['id'], grp['name'], ' '.join(add))

            if not quiet and 'members' in grp:
                show_legend = any(bool(x[2]) for x in grp['members']) or \
                    show_legend
                l = ["%s%s" % ('*' if x[2] else '', x[1])
                     for x in grp['members']]
                print "\t\tMembers: %s" % ', '.join(l)
        if not quiet and show_legend:
            print "* = group admin"
        return retval


    @authenticate()
    def machine_list(self, verbose=False, customer_id=None):
        retval = vaultReply(self.vault.machine_list(self.authtok, customer_id),
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

        return retval


    @authenticate()
    def customer_list(self, customer_id=None):
        """List customers in the vault and possibly corresponding to the needed id
        
        Keywords arguments:
        customer_id -- Id of the needed customer to list

        Receive a list: 
        [{'id': '%d',
         'name': 'blah'},
         {'id': '%d',
         'name': 'blah2'}]
         """
        retval = vaultReply(self.vault.customer_list(self.authtok),
                            "Error listing customers")
        print "Customer list:"
        for x in retval['list']:
            print "c#%d\t%s" % (x['id'], x['name'])
        return retval


