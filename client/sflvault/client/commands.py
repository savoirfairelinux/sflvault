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
import optparse
import os
import re
import sys
import xmlrpclib
import getpass
import shlex
import socket
import platform
if platform.system() != 'Windows':
    import readline

from Crypto.PublicKey import ElGamal
from base64 import b64decode, b64encode
from datetime import *

from sflvault.client.client import SFLvaultClient
from sflvault.common.crypto import *
from sflvault.common import VaultError
from sflvault.client.utils import *
from sflvault.client import ui

class SFLvaultParserError(Exception):
    """For invalid options on the command line"""
    pass


class ExitParserException(Exception):
    """Tells when the parser showed the help for a command."""
    pass

class NoExitParser(optparse.OptionParser):
    """Simple overriding of error handling, so that no sys.exit() is being
    called

    Reference: http://bugs.python.org/issue3079
    """
    def exit(self, status=0, msg=None):
        if msg:
            sys.stderr.write(msg)
        raise ExitParserException()

    def error(self, msg):
        """error(msg : string)

        Print a usage message incorporating 'msg' to stderr and exit.
        If you override this in a subclass, it should not return -- it
        should either exit or raise an exception.
        """
        self.print_usage(sys.stderr)

class SFLvaultShell(object):
    def __init__(self, config, vault=None):
        self.config = config
        self.vault = (vault or SFLvaultClient(config, shell=True))

    def _run(self):
        """Go through all commands on a pseudo-shell, and execute them,
        caching the passphrase at some point."""
        
        print "Welcome to SFLvault. Type 'help' for help."
        prompt = "SFLvault> "
        
        while True:
            cmd = raw_input(prompt)
            if not cmd:
                continue
            
            # Get sys.argv-like parameters
            args = shlex.split(cmd)

            # Local (shell) cmds take precedence over SFLvaultCommand cmds.
            if len(args) and hasattr(self, args[0]):
                getattr(self, args[0])()
            else:
                parser = NoExitParser(usage=optparse.SUPPRESS_USAGE)
                runcmd = SFLvaultCommand(self.config, self.vault, parser)
                try:
                    runcmd._run(args)
                except ExitParserException, e:
                    pass
                
                if hasattr(runcmd, 'next_command') \
                          and platform.system() != 'Windows':
                    print "[Added to shell history: %s]" % runcmd.next_command
                    readline.add_history(runcmd.next_command)

    def quit(self):
        """Quit command, only available in the shell"""
        raise KeyboardInterrupt()

    def exit(self):
        """Exit command, only available in the shell"""
        raise KeyboardInterrupt()


class SFLvaultCommand(object):
    """Parse command line arguments, and call SFLvault commands
    on them.

    Each method of this object are SFLvault commands.  They are called when
    you run ``sflvault connect s#1`` on the command line, or when you run
    ``connect s#1`` from within the shell.
    """
    def __init__(self, config=None, vault=None, parser=None):
        """Create a SFLvaultCommand object

        :param config: config filename to use, required if no vault specified
        :param vault: an existing SFLvaultClient object, otherwise it will be created, using specified config
        :param parser: an option parser, otherwise it will be created (recommended)
        """
        self.parser = (parser or optparse.OptionParser(usage=optparse.SUPPRESS_USAGE))
        
        if not config and not vault:
            raise ValueError("`config` required if `vault` not specified")

        # Use the specified, or create a new one.
        self.vault = (vault or SFLvaultClient(config))

    def _run(self, argv):
        """Run a certain command"""
        self.argv = argv     # Bump the first (command name)
        self.args = []       # Used after a call to _parse()
        self.opts = object() #  idem.

        # Setup default action = help
        action = 'help'
        self.listcmds = False
        if len(self.argv):
            # Take out the action.
            action = self.argv.pop(0)
            if action in ['-h', '--help', '--list-commands']:
                if action == '--list-commands':
                    self.listcmds = True
                action = 'help'

            if action in ['-v', '--version']:
                try:
                    print pkgres.get_distribution('SFLvault_common')
                except pkgres.DistributionNotFound, e:
                    print "SFLvault-common not installed"
                
                print pkgres.get_distribution('SFLvault_client')

                try:
                    print pkgres.get_distribution('SFLvault_server')
                except pkgres.DistributionNotFound, e:
                    print "SFLvault-server not installed"
                return

            # Fix for functions
            action = action.replace('-', '_')
        # Check the first parameter, if it's in the local object.

        # Call it or show the help.
        if not hasattr(self, action):
            print "[SFLvault] Invalid command: %s" % action
            action = 'help'

        self.action = action
        try:
            getattr(self, action)()
        except SFLvaultParserError, e:
            print "[SFLvault] Command line error: %s" % e
            print
            self.help(cmd=action, error=e)
        except AuthenticationError:
            raise
        except VaultError:
            #raise
            pass
        except xmlrpclib.Fault, e:
            # On is_admin check failed, on user authentication failed.
            print "[SFLvault] XML-RPC Fault: %s" % e.faultString
        except xmlrpclib.ProtocolError, e:
            # Server crashed
            print "[SFLvault] XML-RPC end-point failure: %s" % e
        except PermissionError, e:
            print "[SFLvault] Permission denied: %s" % e
        except VaultConfigurationError, e:
            print "[SFLvault] Configuration error: %s" % e
        except RemotingError, e:
            print "[SFLvault] Remoting error: %s" % e
        except ServiceRequireError, e:
            print "[SFLvault] Service-chain setup error: %s" % e
        except DecryptError, e:
            print "[SFLvault] Error decrypting messages: %s" % e.message
        except VaultIDSpecError, e:
            print "[SFLvault] VaultID spec. error: %s" % e
        except socket.error, e:
            print "[SFLvault] Cannot connect to the vault: %s" % e
        except KeyringError, e:
            print "[SFLvault] Keyring error: %s" % e
        

    def _parse(self):
        """Parse the command line options, and fill self.opts and self.args"""
        self.opts, self.args = self.parser.parse_args(args=self.argv)


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
        print "%s version %s" % ('SFLvault-client', pkgres.get_distribution('SFLvault_client').version)
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
                
                    print " %s%s%s" % (x.replace('_','-'),
                                       (18 - len(x)) * ' ',
                                       doc)
            print "---------------------------------------------"
            print "Run: sflvault [command] --help for more details on each of those commands."
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

            try:
                self.parser.parse_args(args=['--help'])
            except ExitParserException, e:
                pass
        else:
            print "No such command"

        print "---------------------------------------------"
            
        if (error):
            print "ERROR calling %s: %s" % (cmd, error)
        return
            

    def user_add(self):
        """Add a user to the vault."""
        self.parser.set_usage("user-add [options] username")
        self.parser.add_option('-a', '--admin', dest="is_admin",
                               action="store_true", default=False,
                               help="Give admin privileges to the added user")

        self._parse()

        if (len(self.args) != 1):
            raise SFLvaultParserError("Invalid number of arguments")
        
        username = self.args[0]
        admin = self.opts.is_admin

        self.vault.user_add(username, admin)


    def customer_add(self):
        """Add a new customer."""
        self.parser.set_usage('customer-add "customer name"')
        self._parse()
        
        if (len(self.args) != 1):
            raise SFLvaultParserError('Invalid number of arguments')

        customer_name = self.args[0]

        ret = self.vault.customer_add(customer_name)
        # For the shell:
        self.next_command = "machine-add -c c#%s " % ret['customer_id']


    def user_del(self):
        """Delete an existing user."""
        self.parser.set_usage("user-del -u <username>")
        self.parser.add_option('-u', dest="username",
                               help="Username to be removed")
        self._parse()

        if not self.opts.username:
            raise SFLvaultParserError("Please specify the user with -u")

        self.vault.user_del(self.opts.username)


    def customer_del(self):
        """Delete an existing customer, it's machines and all services.

        Make sure you have detached all services' childs before removing a
        customer with machines which has services that are parents to other
        services."""
        
        self.parser.set_usage("customer-del -c <customer_id>")
        self.parser.add_option('-c', dest="customer_id", default=None,
                               help="Customer to be removed")
        self._parse()

        if not self.opts.customer_id:
            raise SFLvaultParserError("customer_id is required.")

        customer_id = self.vault.vaultId(self.opts.customer_id, 'c')
        self.vault.customer_del(customer_id)


    def machine_del(self):
        """Delete an existing machine, including all services.

        Make sure you have detached all services' childs before removing
        a machine which has services that are parents to other services.
        """        
        self.parser.set_usage("machine-del -m <machine_id>")
        self.parser.add_option('-m', dest="machine_id", default=None,
                               help="Machine to be removed")
        self._parse()

        if not self.opts.machine_id:
            raise SFLvaultParserError("machine_id is required")

        machine_id = self.vault.vaultId(self.opts.machine_id, 'm')
        self.vault.machine_del(machine_id)


    def service_del(self):
        """Delete an existing service. Make sure you have detached all
        childs before removing a parent service."""
        self.parser.set_usage("service-del -s <service_id>")
        self.parser.add_option('-s', dest="service_id", default=None,
                               help="Service to be removed")
        self._parse()

        if not self.opts.service_id:
            raise SFLvaultParserError("service_id is required")

        service_id = self.vault.vaultId(self.opts.service_id, 's')
        self.vault.service_del(service_id)
        

    def machine_add(self):
        """Add a new machine."""
        self.parser.set_usage('machine-add -n "machine name" -c <customer_id> [options]')
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
        ret = self.vault.machine_add(customer_id, o.name, o.fqdn,
                                     o.ip, o.location, o.notes)
        # For the shell:
        self.next_command = "service-add -m m#%s -u " % ret['machine_id']



    def _service_clean_url(self, url):
        """Remove password in URL, and notify about rewrite."""
        # Rewrite url if a password was included... strip the port and
        #       username from the URL too.
        url = urlparse.urlparse(url)
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

            print "NOTE: Do not specify password in URL. Rewritten as: %s" % url
            return url
        else:
            return False


    def service_add(self):
        """Add a service to a particular machine.

        The secret/password/authentication key will be asked in the
        interactive prompt.

        Note : Passwords will never be taken from the URL when invoked on the
               command-line, to prevent sensitive information being held in
               history.
        """
        self.parser.set_usage("service-add -u <url> -m <machine_id> -g <group_id> [options]")
        self.parser.add_option('-m', '--machine', dest="machine_id",
                               help="Attach Service to Machine #, as "\
                                    "'m#123', '123' or an alias")
        self.parser.add_option('-u', '--url', dest="url",
                               help="Service URL, full proto://[username@]"\
                               "fqdn.example.org[:port][/path[#fragment]], "\
                               "WITHOUT the secret.")

        self.parser.add_option('-p', '--parent', dest="parent_id",
                               help="Make this Service child of Parent "\
                                    "Service #")
        self.parser.add_option('-g', '--group', dest="group_ids",
                               action="append", type="string",
                               help="Access group_id for this service, as "\
                               "'g#123' or '123'. Use group-list to view "\
                               "complete list. You can specify multiple groups")
        self.parser.add_option('--notes', dest="notes",
                               help="Notes about the service, references, "\
                                    "URLs.")
        self.parser.add_option('--metadata', dest="metadata",
                               action="append", type="string",
                               help="Add metadata to this service. Specify as key=value. "\
                                    "This option can appear more than once.")
        self._parse()

        for x in ('url', 'machine_id', 'group_ids'):
            if not getattr(self.opts, x):
                raise SFLvaultParserError("Required parameter '%s' omitted" % x)
        o = self.opts

        rewritten_url = self._service_clean_url(o.url)
        url = rewritten_url if rewritten_url else o.url

        secret = ask_for_service_password(edit=True, url=url)

        machine_id = 0
        parent_id = 0
        group_ids = []
        if o.machine_id:
            machine_id = self.vault.vaultId(o.machine_id, 'm')
        if o.parent_id:
            parent_id = self.vault.vaultId(o.parent_id, 's')
        if o.group_ids:
            group_ids = [self.vault.vaultId(g, 'g') for g in o.group_ids]
        metadata = {}
        if o.metadata:
            for s in o.metadata:
                if '=' not in s:
                    raise SFLvaultParserError("Missing '=' in " \
                                              "metadata option: '%s'" % s)
                key, val = s.split('=', 1)
                metadata[key] = val

        # WARNING: we should check if server supports "metadata" before sending
        self.vault.service_add(machine_id, parent_id, url, group_ids, secret,
                               o.notes, metadata)

    def service_edit(self):
        """Edit service informations."""
        # TODO: implement -s, -m an d-c for those EDIT things..
        self._something_edit("service-edit [service_id]",
                             'service_id', 's',
                             self.vault.service_get,
                             self.vault.service_put,
                             ui.ServiceEditDialogDisplay,
                             'service-edit aborted',
                             decrypt=False)
    def machine_edit(self):
        """Edit machine informations."""
        self._something_edit("machine-edit [machine_id]",
                             'machine_id', 'm',
                             self.vault.machine_get,
                             self.vault.machine_put,
                             ui.MachineEditDialogDisplay,
                             'machine-edit aborted')
    def customer_edit(self):
        """Edit customer informations."""
        self._something_edit("customer-edit [customer_id]",
                             'customer_id', 'c',
                             self.vault.customer_get,
                             self.vault.customer_put,
                             ui.CustomerEditDialogDisplay,
                             'customer-edit aborted')
    def group_edit(self):
        """Edit Group informations"""
        self._something_edit("group-edit [group_id]",
                             'group_id', 'g',
                             self.vault.group_get,
                             self.vault.group_put,
                             ui.GroupEditDialogDisplay,
                             'group-edit aborted')
    def _something_edit(self, usage, required_args, vault_id_type,
                        get_function, put_function, ui_class, abort_message,
                        **kwargs):

        self.parser.set_usage(usage)
        self._parse()

        if not len(self.args):
            raise SFLvaultParserError("Required argument: %s" % required_args)

        thing_id = self.vault.vaultId(self.args[0], vault_id_type)

        # kwargs can contain 'decrypt=False', see service_edit.
        thing = get_function(thing_id, **kwargs)

        if get_function == self.vault.service_get and \
                not thing.get('cryptsymkey'):
            raise PermissionError("You don't have access to that service.  You cannot modify it.")

        try:
            dialog = ui_class(thing)
            save, data = dialog.run()
        except TypeError, e:
            print "W00ps!  The shell GUI doesn't support certain operations, like copy and pasting, or specially weird characters."
            print "In fact, most terminal support doing SHIFT+Middle_Button to paste the text as if the user has typed it, instead of sending Button2 events."
            print "Try it out, hope this helps."
            return

        if save:
            print "Sending data to vault..."
            put_function(thing_id, data)
        else:
            print abort_message


    def service_passwd(self):
        """Change the password for a service.

        Do not specify password on command line, it will be asked on the
        next line.
        """
        self.parser.set_usage("service-passwd <service_id>")
        self._parse()

        if not len(self.args):
            raise SFLvaultParserError("Required argument: service_id")

        service_id = self.vault.vaultId(self.args[0], 's')

        serv = self.vault.service_get(service_id)

        newsecret = ask_for_service_password(edit=True, url=serv['url'])

        self.vault.service_passwd(service_id, newsecret)


    def alias(self):
        """Set an alias, local shortcut to VaultIDs (s#123, m#87, etc..)

        List, view or set an alias."""
        self.parser.set_usage("alias [options] [alias [VaultID]]")

        self.parser.add_option('-d', '--delete', dest="delete",
                               metavar="ALIAS", help="Delete the given alias")

        self._parse()

        if self.opts.delete:
            res = self.vault.cfg.alias_del(self.opts.delete)

            if res:
                print "Alias removed"
            else:
                print "No such alias"

        elif len(self.args) == 0:
            # List aliases
            l = self.vault.cfg.alias_list()
            print "Aliased VaultIDs:"
            for x in l:
                print "\t%s\t%s" % (x[0], x[1])

        elif len(self.args) == 1:
            # Show this alias's value
            a = self.vault.cfg.alias_get(self.args[0])
            if a:
                print "Aliased VaultID:"
                print "\t%s\t%s" % (self.args[0], a)
            else:
                print "Invalid alias"

        elif len(self.args) == 2:
            try:
                r = self.vault.cfg.alias_add(self.args[0], self.args[1])
            except ValueError, e:
                raise SFLvaultParserError(str(e))

            print "Alias added"

        else:
            raise SFLvaultParserError("Invalid number of parameters")


    def customer_list(self):
        """List existing customers.

        This option takes no argument, it just lists customers with their IDs."""
        self._parse()
        
        if len(self.args):
            raise SFLvaultParserError('Invalid number of arguments')

        self.vault.customer_list()

    def user_list(self):
        """List existing users.

        This option takes no argument, it lists the current users and their
        privileges."""
        self.parser.set_usage("user-list [-g]")
        self.parser.add_option('-g', '--groups', default=False,
                               action="store_true", dest="groups",
                               help="List user's group infos")
        self._parse()

        if len(self.args):
            raise SFLvaultParserError("Invalid number of arguments")

        self.vault.user_list(self.opts.groups)


    def _group_service_options(self):
        self.parser.add_option('-g', dest="group_id",
                               help="Group to add the service to")
        self.parser.add_option('-s', dest="service_id",
                               help="Service to be added")

    def _group_service_parse(self):
        if not self.opts.group_id or not self.opts.service_id:
            raise SFLvaultParserError("-g and -s options required")

        self.opts.group_id = self.vault.vaultId(self.opts.group_id, 'g')
        self.opts.service_id = self.vault.vaultId(self.opts.service_id, 's')

    def group_add_service(self):
        """Add a service to a group, doing necessary re-encryption"""
        self.parser.set_usage("group-add-service -g <group_id> -s <service_id>")
        self._group_service_options()
        self._parse()

        self._group_service_parse()
        
        self.vault.group_add_service(self.opts.group_id, self.opts.service_id)

    def group_del_service(self):
        """Remove a service from a group"""
        self.parser.set_usage("group-del-service -g <group_id> -s <service_id>")
        self._group_service_options()
        self._parse()

        self._group_service_parse()
        
        self.vault.group_del_service(self.opts.group_id, self.opts.service_id)


    def _group_user_options(self):
        self.parser.add_option('-g', dest="group_id",
                               help="Group to add the service to")
        self.parser.add_option('-u', dest="user",
                               help="Service to be added")

    def _group_user_parse(self):
        if not self.opts.group_id or not self.opts.user:
            raise SFLvaultParserError("-g and -u options required")
        
        self.opts.group_id = self.vault.vaultId(self.opts.group_id, 'g')

    def group_add_user(self):
        """Add a user to a group, doing necessary re-encryption"""
        self.parser.set_usage("group-add-user [-a] -g <group_id> -u <user>")
        self.parser.add_option('-a', action="store_true", dest='is_admin',
                               default=False, help="Mark as group admin")
        self._group_user_options()
        self._parse()
        self._group_user_parse()
        
        self.vault.group_add_user(self.opts.group_id, self.opts.user,
                                  self.opts.is_admin)

    def group_del_user(self):
        """Remove a user from a group"""
        self.parser.set_usage("group-del-user -g <group_id> -u <user>")
        self._group_user_options()
        self._parse()

        self._group_user_parse()
        
        self.vault.group_del_user(self.opts.group_id, self.opts.user)

    def group_del(self):
        """Remove a group from the vault

        For this to be successful, the group must have no more services
        associated with it."""
        self.parser.set_usage("group-del -g <group_id>")
        self.parser.add_option('-g', dest="group_id", default=None,
                               help="Group to be removed")
        self._parse()
        
        if not self.opts.group_id:
            raise SFLvaultParserError("group_id is required")

        group_id = self.vault.vaultId(self.opts.group_id, 'g')
        self.vault.group_del(group_id)

    def group_add(self):
        """Add a group to the vault

        This command accepts a group name (as string) as first and only
        parameter.
        """
        self.parser.set_usage('group-add "group name"')
        self._parse()

        if len(self.args) != 1:
            raise SFLvaultParserError("Group name (as string) required")

        self.vault.group_add(self.args[0])


    def group_list(self):
        """List existing groups."""
        self.parser.set_usage("group-list [options]")
        self.parser.add_option('-q', dest='quiet', default=False,
                               action="store_true", help="Hide members")
        self._parse()

        if len(self.args):
            raise SFLvaultParserError("Invalid number of arguments")

        self.vault.group_list(self.opts.quiet)


    def machine_list(self):
        """List existing machines.

        This command will list all machines in the vault's database."""
        ## TODO: add support for listing only machines of a certain c#id
        #        (customer_id)
        self.parser.set_usage("machine-list [options]")
        self.parser.add_option('-v', '--verbose', action="store_true",
                               dest='verbose', default=False,
                               help="Enable verbose output (location and notes)")
        self.parser.add_option('-c', '--customer', dest='customer_id',
                               help="Customer id")
        self._parse()

        customer_id = None
        if self.opts.customer_id:
            customer_id = self.vault.vaultId(self.opts.customer_id, 'c')

        if len(self.args):
            raise SFLvaultParserError("Invalid number of arguments")

        self.vault.machine_list(self.opts.verbose, customer_id)


    def user_passwd(self):
        """Change the passphrase protecting your local private key"""
        self.parser.set_usage("user-passwd")
        self._parse()

        if len(self.args) != 0:
            raise SFLvaultParserError("user-passwd takes no arguments")

        self.vault.user_passwd()

    def user_setup(self):
        """Setup a new user on the vault.

        Call this after an admin has called `user-add` on the vault.
        
        username  - the username used in the `user-add` call.
        vault_url - the URL (http://example.org:port/vault/rpc) to the
                    vault"""
        
        self.parser.set_usage("user-setup <username> <vault_url>")
        self._parse()
        
        if len(self.args) != 2:
            raise SFLvaultParserError("Invalid number of arguments")

        username = self.args[0]
        url      = self.args[1]

        self.vault.user_setup(username, url)

    def show(self):
        """Show informations to connect to a particular service.

        VaultID - service ID as 's#123', '123', or alias pointing to a service
                  ID."""
        self.parser.set_usage("show [options] <service_id>")
        self.parser.add_option('-q', '--quiet', dest="quiet",
                               action="store_false", default=True,
                               help="Show notes, locations, groups")
        self._parse()

        if len(self.args) != 1:
            raise SFLvaultParserError("Invalid number of arguments")

        vid = self.vault.vaultId(self.args[0], 's')

        self.vault.show(vid, self.opts.quiet, self.opts.quiet)




    def connect(self):
        """Connect to a remote SSH host, sending password on the way.

        VaultID - service ID as 's#123', '123', or alias pointing to a service
                  ID."""
        # Chop in two parts
        self.parser.set_usage("connect [opts] VaultID")
        self.parser.add_option('-a', '--alias', dest="alias",
                               default=None,
                               help="Add an alias to that service at the same "\
                                    "time")
        self.parser.add_option('-s', '--show', dest="show",
                               default=False, action="store_true",
                               help="Show the credentials before connecting")
        self._parse()

        if len(self.args) < 1:
            raise SFLvaultParserError("Invalid number of arguments")
        
        where = self.args[0]
        vid = self.vault.vaultId(where, 's') # In case we want to add an alias
        command_line = self.args[1:]

        if self.opts.alias:
            try:
                al = "s#%d" % vid
                if command_line:
                    al += " " + ' '.join(command_line)
                r = self.vault.cfg.alias_add(self.opts.alias, al)
            except ValueError, e:
                raise SFLvaultParserError(str(e))
            print "Alias added"

        # Grab alias's arguments if they exist...
        alias = self.vault.cfg.alias_get(where)
        if alias:
            chunks = alias.split()
            if len(chunks) > 1:
                command_line += chunks[1:]
            where = chunks[0]

        vid = self.vault.vaultId(where, 's')

        self.vault.connect(vid, self.opts.show, command_line=command_line)



    def search(self):
        """Search the vault for the specified keywords."""
        self.parser.set_usage('search [opts] keyword1 ["key word2" ...]')
        self.parser.add_option('-g', '--group', dest="groups",
                               action="append", type="string",
                               help="Search in these groups only")
        self.parser.add_option('-q', '--quiet', dest="verbose",
                               action="store_false", default=True,
                               help="Don't show verbose output (includes notes, location)")
        
        self.parser.add_option('-m', '--machine', dest="machines",
                               action="append", type="string",
                               help="Filter results on these machines only")

        self.parser.add_option('-c', '--customer', dest="customers",
                               action="append", type="string",
                               help="Filter results on these customers only")

        self._parse()

        if not len(self.args):
            raise SFLvaultParserError("Search terms required")

        # Get the values for each filter spec..
        fields = {'groups': 'g',
                  'machines': 'm',
                  'customers': 'c'}
        filters = {}
        for f in fields.keys():
            criteria = None
            if getattr(self.opts, f):
                criteria = [self.vault.vaultId(x, fields[f])
                            for x in getattr(self.opts, f)]
            filters[f] = criteria

        self.vault.search(self.args, filters or None, self.opts.verbose)

    def wallet(self):
        """Put your SFLvault password in a wallet"""
        self.parser.set_usage('wallet [num]')
        self._parse()

        if len(self.args) == 0:
            for i, name, obj, status, current in self.vault.cfg.wallet_list():
                print "%s. %s - %s%s" % (i, name, status,
                                         " (*current)" if current else '')
            print
            print "Execute 'wallet <num>' to change wallet"
            return

        # Otherwise
        id = self.args[0]
        lst = self.vault.cfg.wallet_list()
        ids = [x[0] for x in lst]

        if id == '0':
            self.vault.cfg.wallet_set(None, None)
            self.vault.set_getpassfunc(None)
            print "Keyring disabled"
            return

        if id not in ids:
            raise SFLvaultParserError("Invalid wallet ID. Try `wallet` without parameters")

        # Make sure the wallet is supported
        self.vault.cfg.wallet_test([x[1] for x in lst if x[0] == id][0])

        try:
            passwd = getpass.getpass("Enter your current vault password: ")
            self.vault.cfg.wallet_set(id, passwd)
        except KeyringError, e:
            print "[SFLvault] %s" % e
            return False
        print "Keyring set and password saved"



class SFLvaultCompleter:
    def __init__(self, namespace):
        self.namespace = namespace
        self.matches = []

    def complete(self, text, state):
        if state == 0:
            self.matches = self.global_matches(text)
        try:
            return self.matches[state]
        except IndexError:
            return None

    def global_matches(self, text):
        matches = []
        for word in self.namespace:
            if word.find(text,0,len(text)) == 0:
                matches.append(word)
        return matches

###
### Execute requested command-line command
###    

# Default configuration file
if platform.system() == 'Windows':
    CONFIG_FILE = '~/Application Data/SFLvault/config.ini'
else:
    CONFIG_FILE = '~/.sflvault/config'
# Environment variable to override default config file.
CONFIG_FILE_ENV = 'SFLVAULT_CONFIG'

def main():
    # Call the appropriate function of the 'f' object, according to 'action'
    func_list = []
    for onefunc in dir(SFLvaultCommand):
        if onefunc[0] != '_':
            func_list.append(onefunc.replace('_', '-'))

    if platform.system() != 'Windows':
        readline.set_completer_delims('_')
        readline.set_completer(SFLvaultCompleter(func_list).complete)
        readline.parse_and_bind("tab: complete")

    # Set the output to UTF-8 if it's not set by the terminal (for PIPES
    # redirection)
    # See http://stackoverflow.com/questions/492483/setting-the-correct-encoding-when-piping-stdout-in-python
    if sys.stdout.encoding is None:
        import codecs
        sys.stdout = codecs.getwriter('utf8')(sys.stdout)

    # Extract the '-i "identity"' before starting if present.
    args = sys.argv[:]
    identity = None
    if len(args) > 1 and args[1] == '-i':
        del args[1]
        if len(args) == 1 or args[1].startswith('-'):
            print "Error: Identity required after -i"
            sys.exit()
        identity = args.pop(1)

    config_file = CONFIG_FILE
    if identity:
        config_file = "%s.%s" % (CONFIG_FILE, identity)
        print "NOTICE: USING VAULT IDENTITY: %s  (in %s)" % (identity, config_file)
    elif CONFIG_FILE_ENV in os.environ:
        config_file = os.environ[CONFIG_FILE_ENV]

    if len(args) == 1 or args[1] == 'shell':
        s = SFLvaultShell(config=config_file)
        try:
            s._run()
        except (KeyboardInterrupt, EOFError), e:
            print "\nExiting."
            sys.exit()
    else:
        f = SFLvaultCommand(config=config_file)
        f._run(args[1:])
    

# For wrappers.
if __name__ == "__main__":

    main()
