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

__version__ = __import__('pkg_resources').get_distribution('SFLvault').version

# TODO: DECOUPLE CONFIG STUFF FROM THE SFLvaultClient OBJECT
# THIS SHOULD STRICTLY BE IN CLI-CLIENT CODE.
CONFIG_FILE = '~/.sflvault/config'
from ConfigParser import ConfigParser

import xmlrpclib
import getpass
import sys
import re
import os

from decorator import decorator
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
            
        privpass = randfunc(len(privpass))
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
### On définit les fonctions qui vont traiter chaque sorte de requête.
###
class SFLvaultClient(object):
    """Main SFLvault Client object.

    Use this object to connect to the vault and script it if necessary.
    
    This is the object all clients will use to communicate with a remote
    or local Vault.
    """
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
    def del_service(self, service_id):
        retval = self.vault.delservice(self.authtok, service_id)

        if retval['error']:
            print "Error: %s" % retval['message']

            if retval.has_key('childs'):
                print "Those services rely on services you were going "\
                      "to delete:"
                for x in retval['childs']:
                    print "     s#%s%s%s" % (x['id'],
                                             ' ' * (6 - len(str(x['id']))),
                                             x['url'])
        else:
            print "Success: %s" % retval['message']
        

    @authenticate()
    def add_customer(self, customer_name):
        retval = vaultReply(self.vault.addcustomer(self.authtok,
                                                   customer_name),
                            "Error adding customer")

        print "Success: %s" % retval['message']
        print "New customer ID: c#%d" % retval['customer_id']


    @authenticate()
    def add_machine(self, customer_id, name, fqdn, ip, location, notes):
        """Add a machine to the database."""
        # customer_id REQUIRED
        retval = vaultReply(self.vault.addmachine(self.authtok,
                                                  int(customer_id),
                                                  name or '', fqdn or '',
                                                  ip or '', location or '',
                                                  notes or ''),
                            "Error adding machine")
        print "Success: %s" % retval['message']
        print "New machine ID: m#%d" % int(retval['machine_id'])


    @authenticate()
    def add_service(self, machine_id, parent_service_id, url, group_id, secret,
                    notes):
        """Add a service to the Vault's database.

        machine_id - A m#id machine identifier. Specify either machine_id or
                    parent_service_id. 
        parent_service_id - A s#id, parent service ID, to which you should
                            connect before connecting to the service you're
                            adding. Specify 0 of None if no parent exist.
                            If you set this, machine_id is disregarded.
        url - URL of the service, with username, port and path if non-standard.
        group_id - Group of the service. See `list-groups`
        notes - Simple text field, with notes.
        secret - Password for the service. Plain-text.
        """

        # TODO: accept group_id as group_ids, accept list and send list.

        retval = vaultReply(self.vault.addservice(self.authtok,
                                                  int(machine_id),
                                                  int(parent_service_id),
                                                  url,
                                                  int(group_id), secret,
                                                  notes or ''),
                            "Error adding service")

        print "Success: %s" % retval['message']
        print "New service ID: s#%d" % retval['service_id']

    @authenticate()
    def analyze(self, user):
        """Analyze the status of ciphers for a certain user.

        user - user_id or username
        """
        retval = vaultReply(self.vault.analyze(self.authtok, user),
                            "Error analyzing user %s " % user)

        print "Success: %s" % retval['message']

        # Report as received by XML-RPC:
        #report['total_services'] = len(all_set)
        #report['total_ciphers'] = len(ciph_set)
        #report['missing_ciphers'] = len(missing_set)
        #report['missing_groups'] = missing_groups (dict(id: group_name))
        #report['over_ciphers'] = len(over_set)
        #report['over_groups'] = over_groups (dict(id: group_name))

        print '-' * 79
        print "User should have access to:  %d services" % \
                                            retval['total_services']
        print "User has access to:          %d services's ciphers" % \
                                            retval['total_ciphers']
        print '-' * 79
        print "There are:                   %d missing ciphers" % \
                                            retval['missing_ciphers']
        print "There are:                   %d ciphers to be removed" % \
                                            retval['over_ciphers']
        print '-' * 79
        if retval['missing_ciphers']:
            # Print the groups to be re-granted
            print "Groups to be re-granted to complete membership:"
            for x in retval['missing_groups'].keys():
                print "    g#%s  %s" % (x, retval['missing_groups'][x])
            print '-' * 79

        if retval['over_ciphers']:
            # Print the groups to be revoked as quickly as possible
            print "Groups to be revoked on user to clean database:"
            for x in retval['over_groups'].keys():
                print "    g#%s  %s" % (x, retval['over_groups'][x])
            print '-' * 79
                        
        print "Cleaned:                     %d ciphers "\
              "(from deleted services)" % retval['cleaned_ciphers']
        print '-' * 79
        print "End of analysis report"


    @authenticate()
    def revoke(self, user, groups):
        """Revoke permissions to certain groups for a given user

        user   - a required username
        groups - array of group_ids to grant to user
        """
        retval = vaultReply(self.vault.revoke(self.authtok, user, groups),
                            "Error revoking permissions.")

        print "Success: %s" % retval['message']

        pprint(retval['service_ids'])


    @authenticate(True)
    def grant(self, user, groups):
        """Add permissions to a certain user for certain groups.

        user   - a required username
        groups - array of group_ids to grant to user"""
        retval = vaultReply(self.vault.grant(self.authtok, user, groups),
                            "Error granting group permissions.")

        print "Success: %s" % retval['message']

        total = len(retval['ciphers'])

        if total == 0:
            print "No ciphers received for encoding"
            return

        # Get the pubkey, create an ElGamal object with it.
        his_el = ElGamal.ElGamalobj()
        (his_el.p,
         his_el.g,
         his_el.y) = unserial_elgamal_pubkey(retval['user_pubkey'])

        encstuff = []
        total = len(retval['ciphers'])
        count = 0
        print "Encrypting ciphers for user..."
        for cipher in retval['ciphers']:
            # cipher = {'id': service_id, 'stuff': encrypted_symkey}
            # Decrypt the encrypted_symkey with my privkey
            try:
                aeskey = self.privkey.decrypt(unserial_elgamal_msg(cipher['stuff']))
            except Exception, e:
                raise DecryptError("Unable to decrypt my Usercipher: %s" % e.message)
            
            # Encrypt the symkey with his pubkey
            stuff = serial_elgamal_msg(his_el.encrypt(aeskey, randfunc(32)))
            
            # Report progress
            count += 1
            sys.stdout.write("\r  %d of %d " % (count, total))
            sys.stdout.flush()
            
            # Add to the list to be returned in grantupdate() call.
            encstuff.append({'id': cipher['id'],
                             'stuff': stuff})

        sys.stdout.write("\ndone.\n")

        # Delete private key in this client, so that we ask the passphrase
        # again to push the grant update. (NOTE: for now, if you remove this
        # it will still ask  your passphrase.. since there is no check for
        # that at the moment)
        del(self.privkey)

        # Push the ciphers up to the Vault
        self.grantupdate(retval['user_id'], encstuff)

    @authenticate()
    def grantupdate(self, user, ciphers):
        """Close the loop with grant(), and send the ciphers back to the
        Vault.

        user - user_id or username
        ciphers - list of dicts {'id': service_id, 'stuff': encrypted_cipher}
        """
        retval = vaultReply(self.vault.grantupdate(self.authtok, user,
                                                   ciphers),
                            "Error sending encrypted ciphers to the Vault.")

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

        print "You will need a passphrase to secure your private key. The"
        print "encrypted key will be stored on this machine in %s" % CONFIG_FILE
        print '-' * 80
        
        while True:
            privpass = getpass.getpass("Enter passphrase (to secure your private key): ")
            privpass2 = getpass.getpass("Enter passphrase again: ")

            if privpass != privpass2:
                print "Passphrase mismatch, try again."
            elif privpass == '':
                print "Passphrase cannot be null."
            else:
                # Ok, let's go..
                privpass2 = randfunc(len(privpass2))
                break

        
        print "Sending request to vault..."
        # Send it to the vault, with username
        retval = vaultReply(self.vault.setup(username,
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
                     encrypt_privkey(serial_elgamal_privkey([eg.p, eg.x, \
                                                             eg.g, eg.y]),
                                     privpass))
        privpass = randfunc(len(privpass))
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
        retval = vaultReply(self.vault.search(self.authtok, query, verbose),
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
                #print "%s" % (spc2) + ' ' * 6 + '-' * (74 - len(spc2))
                print ""
                for s_id, s in m['services'].items():
                    level = 2
                    # TODO: display service infos
                    add = ' ' * (4 + len(s_id))
                    p_id = s.get('parent_service_id')
                    print "%ss#%s  %s%s" % (spc2, s_id, s['url'],
                                            ("   (depends: s#%s)" % \
                                             p_id if p_id else ''))
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
                    raise DecryptError("Unable to decrypt Usercipher.")
            
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
                raise RemotingError("We don't have access to password for service %s" % x['url'])
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
        
        to_clean = []  # Expired users to be removed
        for x in retval['list']:
            add = ''
            if x['is_admin']:
                add += ' [is admin]'
            if x['setup_expired']:
                add += ' [setup expired]'
                to_clean.append(x['username'])
            if x['waiting_setup'] and not x['setup_expired']:
                add += ' [in setup process]'

            # TODO: load the xmlrpclib.DateTime object into something more fun
            #       to deal with! Some day..
            print "u#%d\t%s\t%s %s" % (x['id'], x['username'],
                                       x['created_stamp'], add)

        print '-' * 80

        if len(to_clean):
            print "There are expired users. To remove them, run:"
            for usr in to_clean:
                print "   sflvault del-user %s" % usr
        

    @authenticate()
    def add_group(self, group_name):
        """Add a named group to the Vault. Return the group id."""
        retval = vaultReply(self.vault.addgroup(self.authtok, group_name),
                            "Error adding group")

        print "Success: %s " % retval['message']
        print "New group id: g#%d" % retval['group_id']


    @authenticate()
    def list_groups(self):
        """Simply list the available groups"""
        retval = vaultReply(self.vault.listgroups(self.authtok),
                            "Error listing groups")

        print "Groups:"

        for x in retval['list']:
            print "\tg#%d\t%s" % (x['id'], x['name'])


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

