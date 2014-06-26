# -=- encoding: utf-8 -=-
#
# SFLvault - Secure networked password store and credentials manager.
#
# Copyright (C) 2009  Savoir-faire Linux inc.
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

from sflvault.client.services import *

class demo(ShellService):
    """Demo service handler - Simple interaction

    This implements the demo:// scheme handler.
    """

    # This service handler doesn't provide anything, so it must be at
    # the end of the chain.

    def required(self, req=None):
        """Verify provided modes.
        
        See ssh service handle for documentation of `required`
        """

        if self.provides(req):
            self.provides_modes = set([req])
        else:
            # Sorry, we don't know what you're talking about :)
            raise ServiceRequireError("demo module can't provide '%s'" % req)
        
        if not self.parent:
            raise ServiceRequireError(
                "demo service can't be executed locally, it has to be behind a SHELL_ACCESS-providing service."
            )

        self.operation_mode = OP_THRGH_SHELL
        return self.parent.required(PROV_SHELL_ACCESS)


    def prework(self):
        print "TESTING123"
        
        class expect_linux_version(ExpectClass):
            """Shortcut pexpect operations.

            You can use pexpect directly. See services in
            sflvault.client.services
            
            From inside this class, you can use:

               self.service.data['plaintext']

            to access the service's data.
            """
            def twosix(self):
                '2.6'
                print ""
                print "DEMO: this machine runs a Linux 2.6 kernel"

            def twofour(self):
                '2.4'
                print ""
                print "DEMO: this machine runs a Linux 2.6 kernel"


        # Bring over here the parent's shell handle.
        cnx = self.parent.shell_handle
        self.shell_handle = cnx

        # Command being sent through the shell.
        cmd = "uname -r"
        cnx.sendline(cmd)
        expect_linux_version(self)
        # For more complex interaction, see sflvault.client.fishlib
        
        print "DEMO: this service's password is: %s" % \
                    self.data['plaintext']

        # Let ssh do the interaction now..
        self.parent.interact()

    # interact() and postwork() inherited
