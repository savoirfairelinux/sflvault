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

from sflvault.client.fishlib import FishClient, showstatus
from sflvault.client.commands import SFLvaultCompleter, NoExitParser
from sflvault.client.commands import ExitParserException, SFLvaultParserError
from sflvault.client.utils import ServiceSwitchException
import shlex
import sys
import optparse
import os
import platform
if platform.system() != 'Windows':
    import readline

class SFLvaultFallback(object):

    def __init__(self, chain, shell_obj):
        # we're to replace completer with new one
        self.parent_completer = readline.get_completer()
        self.parent_completer_last_item = readline.get_current_history_length()\
                                          - 1
        self.func_list = []
        # Services chain
        self.chain = chain
        self.current_shell = shell_obj

        for onefunc in dir(SFLvaultFallback):
            if onefunc[0] != '_':
                self.func_list.append(onefunc)

        readline.set_completer(SFLvaultCompleter(self.func_list).complete)

        self.fish_obj = FishClient(shell_obj)
        self.fish_obj.start()


    # TODO: we need an __getattr__ thing, that's going to catch
    # functions that aren't already defined here.

    def _parse(self):
        """Parse the command line options, and fill self.opts and self.args"""
        (self.opts, self.args) = self.parser.parse_args(args=self.argv)

    def _return_completer(self):
        last_item = readline.get_current_history_length() - 1
        if last_item > self.parent_completer_last_item:
            for tmpid in range(self.parent_completer_last_item, last_item):
                try:
                    readline.remove_history_item(readline.get_current_history_length() - 1)
                except ValueError, e:
                    pass
        readline.set_completer(self.parent_completer)
        print "\nExiting SFLvaultFallback."

    def _run(self):
        """Run the shell, and dispatch commands"""

        while True:
            print "\nWelcome to SFLvaultFallback. Type 'help' for help."
            prompt = "SFLvaultFallback> "

            while True:
                cmd = raw_input(prompt)
                if not cmd:
                    continue

                # Get sys.argv-like parameters
                args = shlex.split(cmd)

                # Local (shell) cmds take precedence over SFLvaultCommand cmds.
                if args[0] == 'quit':
                    self._return_completer()
                    return

                if args[0] in self.func_list:
                    self.parser = NoExitParser(usage=optparse.SUPPRESS_USAGE)
                    self.argv = args
                    self.args = []
                    self.opts = object()

                    try:
                        getattr(self, args[0])()
                    except SFLvaultParserError, e:
                        self.help(cmd=args[0], error=e)
                        pass
                    except ExitParserException, e:
                        pass
                    except UnboundLocalError, e:
                        # TODO: verify if this error can be worked out
                        # differently
                        self.help(cmd=args[0])

                else:
                    self.help()

    def help(self, cmd=None, error=None):
        """Display the list of available commands"""
        
        if not cmd:
            for func in self.func_list:
                doc = getattr(self, func).__doc__
                if doc:
                    doc = doc.split("\n")[0]
                else:
                    doc = '[n/a]'
            
                print "  %s%s%s" % (func,(25 - len(func)) * ' ',doc)
        elif not cmd.startswith('_') and callable(getattr(self, cmd)):
            doc = getattr(self, cmd).__doc__
            if doc:
                print "Help for command: %s" % cmd
                print "---------------------------------------------"
                print doc
            else:
                print "No documentation available for `%s`." % cmd

            print ""
            try:
                self.parser.parse_args(args=['--help'])
            except ExitParserException, e:
                pass
            
        if (error):
            print "ERROR calling %s: %s" % (cmd, error)


    def shells(self):
        """List available shells and switch between them"""
        last = None
        current = self.current_shell
        star = False
        count = 0
        out = {}
        for srv in reversed(self.chain.service_list):
            if hasattr(srv, 'shell_handle'):
                star = (current == srv.shell_handle)
                if last == srv.shell_handle:
                    continue
                count += 1
                print "%d. Shell on service %s%s" % (count, srv,
                                                   ' (current)' if star else '')
                last = srv.shell_handle
                out[str(count)] = srv
        while True:
            shell = raw_input("Switch> ")
            if shell in out:
                srv = out[shell]
                e = ServiceSwitchException("Switching to service %s" % srv)
                e.service = srv
                raise e
            print "Please select a shell from the list"
            break

    def quit(self):
        # Added only for auto completition
        """Quit SFLvaultFallback shell and get back to SSH"""
        pass

    def get(self):
        """Downloading files via SSH using FISH protocol"""
        self.parser.set_usage("get [options]")
        self.parser.add_option('-s', '--source', dest="source",
                               help="Remote machine source filename")
        self.parser.add_option('-d', '--dest', dest="dest",
                               help="Local machine destination filename")

        self._parse()
        
        if len(self.args) != 1:
            raise SFLvaultParserError("Invalid number of arguments")

        if not self.opts.source:
            raise SFLvaultParserError("Required parameter 'source' omitted")

        if not self.opts.dest:
            # we will store in /tmp folder by default
            tmp = self.opts.source.split('/')
            self.opts.dest = '/tmp/' + tmp[-1]
            print "Source file will be stored as: %s" % self.opts.dest
            #raise SFLvaultParserError("Required parameter 'dest' omitted")
        
        try:
            local_file = open(self.opts.dest, 'w')
        except IOError, e:
            raise SFLvaultParserError("I can't create file: %s" % \
                                      self.opts.dest)
        try:
            self.fish_obj.retr(self.opts.source, local_file, showstatus)
        except ValueError, e:
            raise SFLvaultParserError("I can't find file: %s" % \
                                      self.opts.source)

        local_file.close()

    def put(self):
        """Uploading files via SSH using FISH protocol"""
        
        self.parser.set_usage("put [options]")
        self.parser.add_option('-s', '--source', dest="source",
                               help="Locale machine source filename")
        self.parser.add_option('-d', '--dest', dest="dest",
                               help="Remote machine destination filename")

        self._parse()
        
        if len(self.args) != 1:
            raise SFLvaultParserError("Invalid number of arguments")

        if not self.opts.source:
            raise SFLvaultParserError("Required parameter 'source' omitted")

        if not self.opts.dest:
            # we will store in /tmp folder by default
            tmp = self.opts.source.split('/')
            self.opts.dest = '/tmp/' + tmp[-1]
            print "Source file will be stored as: %s" % self.opts.dest
            #raise SFLvaultParserError("Required parameter 'dest' omitted")
        
        try:
            filesize = os.path.getsize(self.opts.source)
        except OSError, e:
            raise SFLvaultParserError("I can't read file: %s" % self.opts.source)

        local_file = open(self.opts.source, 'rb')
        self.fish_obj.stor(self.opts.dest, local_file, filesize, showstatus)
        local_file.close()

