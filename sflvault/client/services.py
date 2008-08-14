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

from sflvault.client.remoting import *
import pexpect
import pxssh
import sys


class ssh(Service):
    """ssh protocol service handler"""

    # Modes this service handler provides
    provides_modes = [PROV_SHELL_ACCESS, PROV_PORT_FORWARD]
    
    # To grab the window changing signals (probably the *last* has to do that)
    #
    #import pexpect, struct, fcntl, termios, signal, sys
    #def sigwinch_passthrough (sig, data):
    #    s = struct.pack("HHHH", 0, 0, 0, 0)
    #    a = struct.unpack('hhhh', fcntl.ioctl(sys.stdout.fileno(), termios.TIOCGWINSZ , s))
    #    global p
    #    p.setwinsize(a[0],a[1])
    #p = pexpect.spawn('/bin/bash') # Note this is global and used in sigwinch_passthrough.
    #signal.signal(signal.SIGWINCH, sigwinch_passthrough)

    def required(self, provide=None):
        """Verify if this service handler can provide `provide` type of connection.

        Child can ask for SHELL_ACCESS or PORT_FORWARD to be provided. It can also
        ask for nothing. It is the case of the last child, which has required()
        invoked with mode=None, since there's no other child that requires something.

        When mode=None, plugin is most probably the last child, and the end to
        which we want to connect."""

        if not self.child and not self.parent:
            # We're alone in the world, we've setting up DIRECT access (spawn a
            # process)
            self.operation_mode = OP_DIRECT
            self.provide_mode = PROV_SHELL_ACCESS
            return True

        # We can provide SHELL or FORWARD, so it's as you wish Mr. required() !
        if self.provides(provide):
            self.provide_mode = provide
        else:
            # Sorry, we don't know what you're talking about :)
            return False
            
        if not self.parent:
            # If there's no parent, then we're going to spawn ourself.
            self.operation_mode = OP_DIRECT

            return True
        else:
            # Otherwise, 'ssh' must be called from within a shell.
            self.operation_mode = OP_THRGH_SHELL
            return self.parent.required(PROV_SHELL_ACCESS)


    def prework(self):
        # Default user:
        user = self.data['loginname'] or 'root'

        #cnx = pxssh.pxssh()
        #res = cnx.login(self.data['hostname'], user, secret, login_timeout=30)
        #del(secret)
        #del(aeskey)
        #if res:
        #    print "LOGIN SUCCESSFUL"
        #    cnx.interact()
        #else:
        #    print "LOGIN FAILED"
        #    sys.exit()
        #sys.exit()

        sshcmd = "ssh -l %s %s" % (user, self.data['hostname'])

        if self.operation_mode == OP_DIRECT:
            print "Trying to login to %s as %s ..." % (self.data['hostname'], user)
            cnx = pexpect.spawn(sshcmd)
        elif self.operation_mode == OP_THRGH_SHELL:
            cnx = self.parent.shell_handle
            cnx.sendline(sshcmd)
        else:
            # NOTE: This should be dead code:
            raise RemotingException("No way to go through there. Woah? How did we get here ?")

        self.shell_handle = cnx

        idx = cnx.expect(['assword:', 'Last login'], timeout=20)
        sys.stdout.write(cnx.before)
        sys.stdout.write(cnx.after)
        
        if idx == 0:
            # Send password
            sys.stdout.write(" [sending password...] ")
            cnx.sendline(self.data['plaintext'])
            idx = cnx.expect([r'\[.*@.*\][$#]'], timeout=10)
            if idx == 0:
                sys.stdout.write(cnx.before)
                sys.stdout.write(cnx.after)
        else:
            # We're in!
            print "We're in! (using shared-key?)"

    def interact(self):
        try:
            self.shell_handle.interact()
        except OSError, e:
            print "SFLvault disconnected."


    def postwork(self):
        
        # If we're the last, let's just close the connection.
        if not self.parent:
            self.shell_handle.close()

    
class su(Service):
    """su app. service handler"""

    # Modes this service handler provides
    provides_modes = [PROV_SHELL_ACCESS]






class vnc(Service):
    """vnc protocol service handler"""

    # Modes this service handler provides
    provides_modes = []

