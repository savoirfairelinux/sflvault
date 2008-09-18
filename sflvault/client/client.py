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
__version__ = __import__('pkg_resources').get_distribution('SFLvault').version


import optparse
import os
import re
import sys
import xmlrpclib
import getpass

from Crypto.PublicKey import ElGamal
from base64 import b64decode, b64encode
from datetime import *

from sflvault.client import SFLvaultClient
from sflvault.lib.common.crypto import *
from sflvault.client.utils import *

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
        self.listcmds = False
        if (len(self.argv)):
            # Take out the action.
            action = self.argv.pop(0)
            if action in ['-h', '--help', '--list-commands']:
                if action == '--list-commands':
                    self.listcmds = True
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


    def help(self, cmd=None, error=None):
        """Print this help.

        You can use:
        
          help [command]

        to get further help for `command`."""

        # For BASH completion.
        if self.listcmds:
            # Show only a list of commands, for bash-completion.
            for x in dir(self):
                if not x.startswith('_') and callable(getattr(self, x)):
                    print x.replace('_', '-')
            sys.exit()

        # Normal help screen.
        print "%s version %s" % (PROGRAM, __version__)
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

    def analyze(self):
        """Analyze user's ciphers state. Check for over-grants and under-grants
        """
        self.parser.set_usage("analyze username|user_id")

        self._parse()

        if len(self.args) != 1:
            raise SFLvaultParserError("Invalid number of arguments, 'user' required.")

        user = self.args[0]
        retval = self.vault.analyze(user)


    def grant(self):
        """Grant group permissions to user.

        Admin privileges required. Use list-groups to have a list."""
        self.parser.set_usage('grant username [options]')
        self.parser.add_option('-g', '--group', dest="groups",
                               action="append", type="string",
                               help="Group membership to grant to user")
        self._parse()

        if (len(self.args) != 1):
            raise SFLvaultParserError("Invalid number of arguments, 'username' required.")

        username = self.args[0]
        groups = [int(x) for x in self.opts.groups]

        # Calls grant and grandupdate on the Vault
        retval = self.vault.grant(username, groups)


    def revoke(self):
        """Revoke group permissions to user.

        Admin privileges required. Use list-groups to have a list."""
        self.parser.set_usage('revoke username [options]')
        self.parser.add_option('-g', '--group', dest="groups",
                               action="append", type="string",
                               help="Group membership to grant to user")
        self._parse()

        if (len(self.args) != 1):
            raise SFLvaultParserError("Invalid number of arguments, 'username' required.")

        username = self.args[0]
        groups = [int(x) for x in self.opts.groups]

        # Calls revoke
        retval = self.vault.revoke(username, groups)


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


    def del_service(self):
        """Delete an existing service. Make sure you have detached all
        childs before removing a parent service."""
        self.parser.set_usage("del-service service_id")
        self._parse()

        if len(self.args) != 1:
            raise SFLvaultParserError("Invalid number of arguments")

        service_id = int(self.args[0])

        self.vault.del_service(service_id)
        

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
        # TODO: support multiple groups (add service in multiple groups)
        self.parser.add_option('-g', '--group', dest="group_id", default='',
                               help="Access group_id for this service, as 'g#123' or '123'. Use list-groups to view complete list.")
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

        # Rewrite url if a password was included... strip the port and
        #       username from the URL too.
        if url.password:
            out = []
            if url.username:
                out.append('%s@' % url.username)
                
            out.append(url.hostname)
            
            if url.port:
                out.append(":%d" % url.port)
            
            url = urlparse.urlunparse((url[0],
                                       ''.join(out),
                                       url[2], url[3], url[4], url[5]))

            print "Do not specify password in URL. Rewritten: %s" % url


        # TODO: plug-in-ize password capture.
        if not secret:
            secret = getpass.getpass("Enter service's password: ")


        machine_id = 0
        parent_id = 0
        group_id = 0
        if o.machine_id:
            machine_id = self.vault.vaultId(o.machine_id, 'm')
        if o.parent_id:
            parent_id = self.vault.vaultId(o.parent_id, 's')
        if o.group_id:
            group_id = self.vault.vaultId(o.group_id, 'g')
            
        self.vault.add_service(machine_id, parent_id, o.url, group_id, secret,
                               o.notes)
        del(secret)

    def chg_service_passwd(self):
        """Change the password for a service

        Do not specify password on command line, it will be asked on the
        next line.
        """
        self.parser.add_option('-s', dest="service_id",
                               help="Service ID for which to change password")
        
        self._parse()

        if not self.opts.service_id:
            raise SFLvaultParserError("Required parameter '-s' omitted")
        
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

    def add_group(self):
        """Add a group to the Vault

        This command accepts a group name (as string) as first and only
        parameter.
        """
        self._parse()

        if len(self.args) != 1:
            raise SFLvaultParserError("Group name (as string) required")

        self.vault.add_group(self.args[0])


    def list_groups(self):
        """List existing groups."""
        self._parse()

        if len(self.args):
            raise SFLvaultParserError("Invalid number of arguments")

        self.vault.list_groups()


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
