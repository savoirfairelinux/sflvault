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

"""Fallback Shell is used when we back off an active shell with the
escape sequence, to get a grip on the built-in FISH functionalities.

Other commands will be implemented in the future, giving ability to
script on the client side things that will be sent to through the shell."""

class SFLvaultFallback(object):
    # TODO: implement this!

    # TODO: we need an __getattr__ thing, that's going to catch
    # functions that aren't already defined here.

    def _run(self):
        """Run the shell, and dispatch commands"""
        while True:
            # TODO: check out readline stuff, change history..
            cmd = raw_input("SFLvaultFallback> ")

            # TODO: dispatch commands

            if cmd == 'quit':
                return

    def get(self):
        """Implement the FISH RETR function"""
        pass

    def put(self):
        """Implement the FISH STOR function"""
        
