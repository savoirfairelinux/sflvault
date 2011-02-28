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

from sflvault.client.remoting import *
from sflvault.client.utils import *
from sflvault.client.fallback import SFLvaultFallback
import struct, fcntl, termios, signal # for term size signaling..
import optparse
import random
import pipes
import time
import sys
import os
import platform
if platform.system() != 'Windows':
    import pexpect

# Enum used in the services' `provides`
PROV_PORT_FORWARD = 'PROV_PORT_FORWARD'
PROV_SHELL_ACCESS = 'PROV_SHELL_ACCESS'
PROV_MYSQL_CONSOLE = 'PROV_MYSQL_CONSOLE'
PROV_POSTGRES_CONSOLE = 'PROV_POSTGRES_CONSOLE'

# Operational modes
OP_DIRECT = 'OP_DIRECT'                # - When, let's say 'ssh' is going to
                                       # spawn a process.
OP_THRGH_FWD = 'OP_THRGH_FWD'          # - When we must go through a port
                                       # that's been forwarded.
                                       # In that case, the parent must provide
                                       # with  forwarded host and port.
OP_THRGH_SHELL = 'OP_THRGH_SHELL'      # - When a command must be sent through
                                       # an open shell



### Service definitions

class ExpectClass(object):
    def __init__(self, service_obj, strings_and_funcs=None):
        # Hold the parent Service object here..
        self.service = service_obj
        self.error = None

        # Quick references..
        self.cnx = self.service.shell_handle

        funcs = []
        strings = []
        if strings_and_funcs:
            for s, f in strings_and_funcs:
                strings.append(s)
                funcs.append(getattr(self, f))
        for x in dir(self):
            if x.startswith('_'):
                continue
            
            func = getattr(self, x)

            if callable(func) and func.__doc__:
                funcs.append(func)
                strings.append(func.__doc__)

        idx = self._expect(strings)

        funcs[idx]()

    def _expect(self, strings):
        """Wrap the expect() call"""
        timeout = self.service.timeout

        try:
            idx = self.cnx.expect(strings, timeout=timeout)
        except pexpect.TIMEOUT, e:
            self._flush()
            if hasattr(self, '_timeout'):
                self._timeout()
            else:
                sys.stdout.write("\nTimed out")

            self.error = "Timed out"
            raise ServiceExpectError("Timed out")

        self._flush()

        return idx
    
    def _flush(self):
        sys.stdout.write(self.cnx.before)
        sys.stdout.write(self.cnx.after)
        sys.stdout.flush()


class ExpectShell(ExpectClass):
    """When initialized, this class will wait for a shell prompt via pexpect
    and call its ``shell`` method when it sees one.

    The shell prompt can be configured for each service using the
    ``shell_prompt`` metadata key.
    """
    def __init__(self, service, strings_and_funcs=None):
        strings_and_funcs = strings_and_funcs[:] if strings_and_funcs else []
        if isinstance(service.data['metadata'], dict):
            prompt = service.data['metadata'].get('prompt') or r'[^ ]*@.*:.*[$#] '
        else:
            prompt = r'[^ ]*@.*:.*[$#] '
        strings_and_funcs.append((prompt, 'shell'))
        ExpectClass.__init__(self, service, strings_and_funcs)

    def shell(self):
        pass


class ShellService(Service):
    """Abstract class for services running over ssh. Helper funcs."""


    def __init__(self, data, timeout=45):
        # Call parent
        Service.__init__(self, data, timeout)
        
    def interact(self):

        # To grab the window changing signals
        def sigwinch_passthrough (sig, data):
            s = struct.pack("HHHH", 0, 0, 0, 0)
            a = struct.unpack('hhhh', fcntl.ioctl(sys.stdout.fileno(),
                                                  termios.TIOCGWINSZ , s))
            self.shell_handle.setwinsize(a[0],a[1])

        # Map window resizing signal to function
        signal.signal(signal.SIGWINCH, sigwinch_passthrough)

        # Call USER's terminal and get term size.
        s = struct.pack("HHHH", 0, 0, 0, 0)
        fd_stdout = sys.stdout.fileno()
        x = fcntl.ioctl(fd_stdout, termios.TIOCGWINSZ, s)
        sz = struct.unpack("HHHH", x)
        # Send to the remote terminals..
        self.shell_handle.setwinsize(sz[0], sz[1])


        try:
            # Go ahead, you're free to go !
            while True:
                self.shell_handle.interact(escape_character=sflvault_escape_chr)
                # Drop in the shell, only if connection is still open
                if not self.shell_handle.isalive():
                    break

                s = SFLvaultFallback(self.chain, self.shell_handle)
                try:
                    s._run()
                except (KeyboardInterrupt, EOFError), e:
                    s._return_completer()
                continue

                # TODO we need to check if shell is still alive

            # Reset signal
            signal.signal(signal.SIGWINCH, signal.SIG_DFL)

            print "[SFLvault] Escaped from %s, calling postwork." % self.__class__.__name__
        except OSError, e:
            print "[SFLvault] %s disconnected: %s" % (self.__class__.__name__,
                                                      e)
            raise e


    def postwork(self):
        # Close any open connection.
        if not self.shell_handle.closed:
            print "Closing connection for service %s" % self
            self.shell_handle.close()
        # NOTE: this will close all the `ssh` tunnel when it was continued
        #       through shells



class ssh(ShellService):
    """ssh protocol service handler"""

    def __init__(self, data, timeout=45):
        # Call parent
        ShellService.__init__(self, data, timeout)
        self.provides_modes = set([PROV_SHELL_ACCESS, PROV_PORT_FORWARD])
        self.local_forwards = []
        self.remote_forwards = []
        # TODO: Add SOCKS forward...
        
    ssh_pki_auth = False   # Overwridden by ssh_pki

    def has_forwards(self):
        """Returns True if we have something to forward"""
        return bool(self.local_forwards) or bool(self.remote_forwards)

    def optparse(self, command_line):
        """Parse the command line for port-forwarding options"""
        parser = optparse.OptionParser(usage=optparse.SUPPRESS_USAGE)
        parser.set_usage('... [-L port:hostname:port [-L ...]] ' \
                         '[-R port:hostname:port [-R ...]]')
        parser.add_option('-L', dest='locals', action='append', type='string',
                          default=[],
                          help="Listen locally, then forward (see man ssh)")
        parser.add_option('-R', dest='remotes', action='append', type='string',
                          default=[],
                          help="Listen remotely, forward locally. ")
        opts, args = parser.parse_args(args=command_line)
        # We shouldn't have remaining arguments
        if args:
            raise RemotingError('Unknown parameters: %s' % args)
        # Save locals and remotes
        def parse_forward(fwd):
            # Return tuples in the form: (bind_address, port, host, hostport)
            el = tuple(fwd.split(':'))
            if len(el) == 3:
                return ('localhost',) + el
            elif len(el) == 4:
                return el
            else:
                raise RemotingError('Parameters to -L or -R must be in the form: [bind_address:]port:host:hostport')

        for l in opts.locals:
            #print "Requesting LOCAL forward for: %s" % l
            self.chain.add_port_forward(None, 'local', *parse_forward(l))
        for r in opts.remotes:
            #print "Requesting REMOTE forward for: %s" % r
            self.chain.add_port_forward(None, 'remote', *parse_forward(r))
        #self.local_forwards = [parse_forward(l) for l in opts.locals]
        #self.remote_forwards = [parse_forward(r) for r in opts.remotes]

    def required(self, req=None):
        """Verify if this service handler can provide `req` type of
        connection.

        Child can ask for SHELL_ACCESS or PORT_FORWARD to be provided. It
        can also ask for nothing. It is the case of the last child, which
        has required() invoked with mode=None, since there's no other
        child that requires something.

        When mode=None, plugin is most probably the last child, and the
        end to which we want to connect.
        """

        if not self.child and not self.parent:
            # We're alone in the world, we've setting up DIRECT access (spawn a
            # process)
            self.operation_mode = OP_DIRECT
            return True

        # Can we provide what you need ?
        if not self.provides(req):
            # Sorry, we don't know what you're talking about :)
            raise ServiceRequireError("ssh module can't provide '%s'" % req)

        if self.ssh_pki_auth and self.parent:
            # If the command line asked it, or we're authenticating through
            # ssh keys, try to make port-forwards.
            if self.parent:
                self.operation_mode = OP_THRGH_FWD
                # Setup port-forwards
                randport = random.randint(58000, 60000)
                self.chain.add_port_forward(self, 'local', 'localhost',
                                            randport, self.url.hostname,
                                            self.url.port or 22)
                self.op_through_host = 'localhost'
                self.op_through_port = randport
            else:
                self.operation_mode = OP_DIRECT

            if self.parent:
                return self.parent.required(PROV_PORT_FORWARD)
            else:
                return True

        if not self.parent:
            # If there's no parent, then we're going to spawn ourself.
            self.operation_mode = OP_DIRECT
        else:
            # Otherwise, 'ssh' must be called from within a shell.
            self.operation_mode = OP_THRGH_SHELL
            # Ask for a PORT_FORWARD if that's what was asked of us,
            # otherwise, just give us a normal shell.
            return self.parent.required(req or PROV_SHELL_ACCESS)

        return True


    def prework(self):

        # Prework classes
        class expect_shell(ExpectShell):

            def terminal_type(self):
                "Terminal type\?.*$"
                sys.stdout.write(" [sending: xterm] ")
                self.cnx.sendline("xterm")
                sys.stdout.flush()
            
            def shell(self):
                pass # We're in :)
            
            def denied(self):
                'Permission denied.*$'
                self.cnx.sendcontrol('c')
                raise ServiceExpectError("Failed to authenticate")
            
            def failed_login(self):
                'assword:'
                self.cnx.sendcontrol('c')
                print ""
                raise ServiceExpectError("Failed to authenticate")

            def are_you_sure(self):
                "(?i)are you sure you want to continue connecting.*\? "
                ans = raw_input()
                self.cnx.sendline(ans)
                expect_shell(self.service)

            def forward_error(self):
                "Privileged ports can only be forwarded by root"
                print ""
                raise ServiceExpectError("Port forward failed.")

        class expect_login(ExpectClass): 
            #forward_error = expect_shell.forward_error

            def sendlogin(self):
                'assword:'
                sys.stdout.write(" [sending password...] ")
                self.cnx.sendline(self.service.data['plaintext'])
                sys.stdout.flush()

                expect_shell(self.service)

            def werein(self):
                'Last login'
                print " [We're in! (using shared-key?)] ",

            def are_you_sure(self):
                "(?i)are you sure you want to continue connecting.*\? "
                # TODO: are you always sure ??
                ans = raw_input()
                self.cnx.sendline(ans)

                expect_login(self.service)

            def remote_host_changed(self):
                "REMOTE HOST IDENTIFICATION HAS CHANGED!"

                ans = raw_input("Would you like SFLvault to remove that offending line and try again (yes/no)? ")
                if ans.lower() == 'yes' or ans.lower() == 'y':
                    idx = self._expect([r"Offending key in ([^:]+):(\d+)"])
                    cmd = 'sed -i %sd "%s"' % (self.cnx.match.group(2),
                                               self.cnx.match.group(1))

                    if self.service.operation_mode in [OP_DIRECT,
                                                       OP_THRGH_FWD]:
                        # Remove the line
                        os.system(cmd)
                    else: # operation_mode == OP_THRGH_SHELL
                        self.cnx.sendline(cmd)

                    raise ServiceExpectError("SFLvault removed offending key. Please try again.")
                else:
                    raise ServiceExpectError("Remote host identification has changed. Please resolve problem.")

                self._expect([pexpect.EOF])
            

        # Default user:
        user = self.url.username or 'root'

        sshcmd = "ssh"
        if self.operation_mode in [OP_DIRECT, OP_THRGH_SHELL]:
            print "\n... Trying to login to %s as %s ..." % (self.url.hostname,
                                                             user)
            sshcmd += " -l %s %s" % (user, self.url.hostname)
            if self.url.port:
                sshcmd += " -p %d" % (self.url.port)
        elif self.operation_mode == OP_THRGH_FWD:
            # Take the bound port on the first (OP_DIRECT) ssh connection.
            port = self.op_through_port
            host = self.op_through_host
            print "... Trying to login to %s (through local port-forward, " \
                  "port %d) as %s ..." % (self.url.hostname, port, user)
            # TODO: Do not take into consideration the `known hosts` list.
            sshcmd += " -l %s %s" % (user,host)
            sshcmd += " -p %d" % (port)
            sshcmd += " -o NoHostAuthenticationForLocalhost=yes"
            #time.sleep(0)

        # Check if we have private key support
        pki_cmd = None
        if self.ssh_pki_auth:
            # Write the private-key to a temp file.
            randfifo = '/tmp/sshpki%d' % random.randint(100000,999999)
            secret = pipes.quote(self.data['plaintext'])
            pki_cmd = "rm -f %s ; touch %s ; chmod 0600 %s ; " \
                      "((echo %s > %s; sleep 4; rm %s) &);" % (randfifo,
                                                               randfifo,
                                                               randfifo,
                                                               secret, randfifo,
                                                               randfifo)
            sshcmd += " -i %s " % randfifo

        #if PROV_PORT_FORWARD in self.provides_modes:
        if self.has_forwards():
            # Do the last forwarding
            sshcmd += " %s %s " % (' '.join(self.local_forwards),
                                   ' '.join(self.remote_forwards))

        if self.operation_mode in [OP_DIRECT, OP_THRGH_FWD]:
            if pki_cmd:
                print "Running SSH+PKI setup..."
                os.system(pki_cmd)
            print "EXECUTING: %s" % sshcmd
            cnx = pexpect.spawn(sshcmd)
        elif self.operation_mode == OP_THRGH_SHELL:
            cnx = self.parent.shell_handle
            if pki_cmd:
                print "Sending SSH+PKI setup..."
                cnx.sendline(pki_cmd)
            print "SENDING LINE: %s" % sshcmd
            cnx.sendline(sshcmd)
        else:
            # NOTE: This should be dead code:
            raise RemotingError("No way to go through there. Woah? How did we get here ?")

        self.shell_handle = cnx

        if self.ssh_pki_auth:
            expect_shell(self)
        else:
            expect_login(self)





class ssh_pki(ssh):
    """SSH with private-key handler"""
    ssh_pki_auth = True   # Overwridden by ssh_pki

    @staticmethod
    def ask_password(edit, parsed_url):
        """Function to grab password"""
        print """Copy and paste the SSH PRIVATE KEY, which looks like:
-----BEGIN (D|R)SA PRIVATE KEY-----
B64DEADBEEF...==
-----END (D|R)SA PRIVATE KEY-----
"""
        pk = []
        while True:
            chunk = raw_input(">>> ")
            pk.append(chunk)
            if '---END' in chunk:
                break
        return '\n'.join(pk)
        


class content(Service):
    """Static content store.  Will store any blob into the database as the secret"""
    @staticmethod
    def ask_password(edit, parsed_url):
        """Function to grab the content and set it as the secret"""
        print """Paste the content to store, and hit Ctrl+C"""
        pk = []
        try:
            while True:
                chunk = raw_input(">>> ")
                pk.append(chunk)
        except KeyboardInterrupt, e:
            print ""
            return '\n'.join(pk)

class sflvault(content):
    """Inherit password entry, when storing other Vault's Private key"""
    pass



# TODO: document that the `sudo` doesn't need a password, it takes the password
# from the parent service.
class sudo(ShellService):
    """sudo app. service handler"""

    provides_modes = set([PROV_SHELL_ACCESS])

    def required(self, req=None):
        """Check requirements for sudo

        See ssh service handle for documentation of `required`
        """

        # We must be over an 'ssh' to do anything!
        if not self.parent or not self.parent.required(PROV_SHELL_ACCESS):
            raise ServiceRequireError("`sudo` must be child of a shell")

        # We can provide SHELL
        if not self.provides(req):
            raise ServiceRequireError("`sudo` module can't provide '%s'" % req)

        # TODO: pass-through PORT_FORWARD provisioning if child supports it..
        return True


    def prework(self):
        # Inherit shell handle
        self.shell_handle = self.parent.shell_handle

        class expect_waitshell(ExpectShell):

            def shell(self):
                return True

            def failed(self):
                'assword:'
                self.cnx.sendintr()
                print ""
                raise ServiceExpectError("Failed to authenticate sudo://")

            def failed2(self):
                'Sorry'
                self.failed()

        class expect_sudowork(ExpectClass):
            def sendpass(self):
                'assword:'

                sys.stdout.write(" [sending password...] ")
                self.cnx.sendline(self.service.parent.data['plaintext'])

                expect_waitshell(self.service)

            def sendpass2(self):
                r'assword for.*:'
                self.sendpass()

        # Send command
        self.shell_handle.sendline('sudo -i')

        expect_sudowork(self)
        
    # Call parent
    #def interact(self):
    # Call parent
    #def postwork(self):

   
class su(ShellService):
    """su app. service handler"""

    provides_modes = set([PROV_SHELL_ACCESS])

    def required(self, req=None):
        """Check requirements for su
        
        See ssh service handle for documentation of `required`
        """

        # We must be over an 'ssh' to do anything!
        if not self.parent or not self.parent.required(PROV_SHELL_ACCESS):
            raise ServiceRequireError("`su` must be child of a shell")

        # We can provide SHELL
        if not self.provides(req):
            raise ServiceRequireError("`su` module can't provide "\
                                      "'%s'" % req)

        # TODO: pass-through PORT_FORWARD provisioning if child supports it..
        return True


    def prework(self):
        # Inherit shell handle
        self.shell_handle = self.parent.shell_handle

        class expect_waitshell(ExpectShell):

            def shell(self):
                return True

            def failed(self):
                'assword:'
                raise ServiceExpectError("Failed to authenticate su://")

            def failed2(self):
                'incorrect'
                self.failed()

        class expect_suwork(ExpectShell):
            def sendpass(self):
                'assword:'

                sys.stdout.write(" [sending password...] ")
                self.cnx.sendline(self.service.data['plaintext'])

                expect_waitshell(self.service)

            def shell(self):
                return True
                

        # Send command
        self.shell_handle.sendline('su %s' % self.url.username or 'root')

        expect_suwork(self)
        
    # Call parent
    #def interact(self):
    # Call parent
    #def postwork(self):



class mysql(ShellService):
    """mysql app. service handler"""

    provides_modes = set([PROV_MYSQL_CONSOLE])
       
    def required(self, req=None):
        """Verify provided modes.
        
        See ssh service handle for documentation of `required`
        """

        if self.provides(req):
            self.provides_modes = set([req])
        else:
            # Sorry, we don't know what you're talking about :)
            raise ServiceRequireError("mysql module can't provide '%s'" % req)
        
        if not self.parent:
            raise ServiceRequireError("mysql service can't be executed locally, it has to be behind a SHELL_ACCESS-providing module.")

        self.operation_mode = OP_THRGH_SHELL
        return self.parent.required(PROV_SHELL_ACCESS)


    def prework(self):

        class expect_mysql_shell(ExpectClass):
            def shell(self):
                'mysql>'
                pass # We're in :)

            def error(self):
                'ERROR \d*'
                raise ServiceExpectError('Failed to authenticate with mysql')

        class expect_mysql(ExpectClass):
            def login(self):
                'assword:'
                sys.stdout.write(" [sending password...] ")
                self.cnx.sendline(self.service.data['plaintext'])

                expect_mysql_shell(self.service)

            def error(self):
                'ERROR \d*'
                raise ServiceExpectError("Failed authentication for mysql "\
                                         "at program launch")
            
            def notfound(self):
                'command not found.*$'
                raise ServiceExpectError('mysql client not installed on server')


        # Bring over here the parent's shell handle.
        cnx = self.parent.shell_handle
        self.shell_handle = cnx

        # Select a database directly ?
        db = ''
        if self.url.path:
            if self.url.path != '/':
                db = self.url.path.lstrip('/')
                
        cmd = "mysql -h %s -u %s -p %s" % (self.url.hostname, self.url.username,
                                           db)

        cnx.sendline(cmd)


        expect_mysql(self)


    # interact() and postwork() inherited
    

class postgres(ShellService):
    """PostgreSQL service handler"""

    provides_modes = set([PROV_POSTGRES_CONSOLE])
       
    def required(self, req=None):
        """Verify provided modes.
        
        See ssh service handle for documentation of `required`
        """

        if self.provides(req):
            self.provides_modes = set([req])
        else:
            # Sorry, we don't know what you're talking about :)
            raise ServiceRequireError("postgres module can't provide '%s'" % req)
        
        if not self.parent:
            raise ServiceRequireError("postgres service can't be executed locally, it has to be behind a SHELL_ACCESS-providing module.")

        self.operation_mode = OP_THRGH_SHELL
        return self.parent.required(PROV_SHELL_ACCESS)


    def prework(self):

        class expect_postgres_shell(ExpectClass):
            def shell(self):
                '\w*=#'
                pass # We're in :)

            def error(self):
                'postgres: FATAL:  password authentication failed \w* "\w*"'
                raise ServiceExpectError('Failed to authenticate with postgres')

        class expect_postgres(ExpectClass):
            def login(self):
                'assword for user \w*:'
                sys.stdout.write(" [sending password...] ")
                self.cnx.sendline(self.service.data['plaintext'])

                expect_postgres_shell(self.service)

            def error(self):
                'postgres: FATAL:  password authentication failed \w* "\w*"'
                raise ServiceExpectError("Failed authentication for postgres "\
                                         "at program launch")
            
            def notfound(self):
                'command not found.*$'
                raise ServiceExpectError('postgres client not installed on server')


        # Bring over here the parent's shell handle.
        cnx = self.parent.shell_handle
        self.shell_handle = cnx

        cmd = "psql -U %s -W -h %s" % (self.url.username, self.url.hostname)

        # Select a port  directly ?
        if int(self.url.port):
            cmd += " -p %s" % self.url.port

        # Select a database directly ?
        db = ''
        if self.url.path:
                if self.url.path != '/':
                    db = self.url.path.lstrip('/')
                    cmd += " -d %s" % db

        cnx.sendline(cmd)

        expect_postgres(self)

    # interact() and postwork() inherited


# TODO: do something :) launch vncviewer! Require a port-forward
# if behind some `ssh`.
class vnc(Service):
    """vnc protocol service handler"""

    # Modes this service handler provides
    provides_modes = set([])

