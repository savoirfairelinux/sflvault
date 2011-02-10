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

"""Several utilities used in the SFLvault client"""

import urlparse
import re
from pkg_resources import iter_entry_points, DistributionNotFound
import platform
if platform.system() != 'Windows':
    import readline


__all__ = ['shred', 'urlparse', 'AuthenticationError', 'PermissionError',
           'VaultIDSpecError', 'VaultConfigurationError', 'RemotingError',
           'ServiceRequireError', 'ServiceExpectError', 'sflvault_escape_chr',
           'ask_for_service_password', 'services_entry_points',
           "ServiceSwitchException", "KeyringError"]


def services_entry_points():
    """Return the list of entry points for the different services."""
    return iter_entry_points('sflvault.services')

#
# Add protocols to urlparse, for correct parsing of ssh and others.
#
urlparse.uses_netloc.extend(['ssh', 'vlc', 'vpn', 'openvpn', 'git',
                             'bzr+ssh', 'vnc', 'mysql', 'sudo', 'su',
                             'psql'] +
                             [x.name for x in services_entry_points()])


# Issue: Ctrl+Alt+;
sflvault_escape_chr = chr(30)


# TO REMOVE: This shred function is useless in python, because of the way
# it manages memory (especially strings)
def shred(var):
    """Tries to wipe out from memory certain variables

    Apparently, Python can't do that, or it depends on the implementation.
    We should find a way to do that"""
    l = len(var)
    var = 'x' * l
    return var





def ask_for_service_password(edit=False, url=None):
    # Use the module's ask_password if it supports one...
    parsed_url = urlparse.urlparse(url)
    for ep in services_entry_points():
        if ep.name == parsed_url.scheme:
            try:
                srvobj = ep.load()
            except DistributionNotFound, e:
                break
            if hasattr(srvobj, 'ask_password'):
                return srvobj.ask_password(edit, parsed_url)

    # Use raw_input so that we see the password. To make sure we enter
    # a valid and the one we want (what if copy&paste didn't work, and
    # you didn't know ?)
    sec = raw_input("Enter new service's password: " if edit
                    else "Enter service's password: ")
    readline.remove_history_item(readline.get_current_history_length() - 1)
    # CSI n F to go back one line. CSI n K to erase the line.
    # See http://en.wikipedia.org/wiki/ANSI_escape_code
    print "\033[1F\033[2K ... password taken ..."
    return sec


### Passwords management exceptions

class KeyringError(Exception):
    pass



### Authentication Exceptions

class AuthenticationError(Exception):
    pass


### Server restrictions errors

class PermissionError(Exception):
    """Raised when server enforces permissions"""
    pass


### VaultError is in SFLvault-common


### Vault-communication Exceptions
    
class VaultIDSpecError(Exception):
    """When bad parameters are passed to vaultId"""
    pass

class VaultConfigurationError(Exception):
    """Except when we're missing some config info."""
    pass

### Remoting Exceptions

class RemotingError(Exception):
    """When something happens in the Remoting mechanisms"""
    pass

class ServiceRequireError(RemotingError):
    """When the required() elements can't do what we want."""
    pass

class ServiceExpectError(RemotingError):
    """When an error occurs in the expected values in prework to set up a
    service.

    We assume the interact() will be called for the parent at that point."""
    pass

class ServiceSwitchException(Exception):
    """Way to switch the active shell"""
    pass


# Flexible URL parser (not RFC compliant, but very flexible for our purpose)
class URLParserError(Exception):
    pass

class URLParser(object):
    """Parses URLs and splits `scheme`, `hostname`, `username`, `port`,
    `path`, `query`, `fragment`, etc.. apart in an string representing an URL

    >>> u = URLParser('http://www.example.com/path')
    >>> u
    ...
    >>> u.hostname
    'www.example.com'
    >>> u.path
    '/path'

    >>> u2 = URLParser('git+ssh://[user@host]@git.example.com/var/www/repos')
    >>> u2.username
    'user@host'
    >>> u2.hostname
    'git.example.com'
    >>> u2.path
    '/var/www/repos'

    >>> u3 = URLParser('https://[user@host]:passwd123@[2009::10:ab]:123/var/my/path?q=hello#frag123')
    >>> u3.scheme
    'https'
    >>> u3.username
    'user@host'
    >>> u3.password
    'passwd123'
    >>> u3.hostname
    '2009::10:ab'
    >>> u3.port
    '123'
    >>> u3.path
    '/var/my/path'
    >>> u3.query
    'q=hello'
    >>> u3.fragment
    'frag123'

    >>> u3.gen_url(with_password=False)  # Default behavior
    'https://[user@host]@[2009::10:ab]:123/var/my/path?q=hello#frag123'
    """
    _regex = re.compile(r"([a-zA-Z0-1+-]+)(://)(((\[([^\]]+)\])|([^@]+))(:([^@]*))?@)?(([^\[/][^:/\?#]+)|(\[([^\]]+)\]))?(:(\d+))?(/([^\?]*))?(\?([^#]*))?(#(.*))?")
    
    def __init__(self, url=None):
        """Parse an URL or create a new empty object"""
        self.scheme = None
        self.username = None
        self.password = None
        self.hostname = None
        self.port = None
        self.path = None
        self.query = None
        self.fragment = None
        if url:
            self._parse(url)

    def _parse(self, url):
        """Extract infos from URLs, and fill in this object"""
        res = self._regex.match(url)
        if not res:
            raise URLParserError('Invalid or malformed URL')
        self.scheme = res.group(1)
        self.username = res.group(6) or res.group(7) or ''
        self.password = res.group(9)
        self.hostname = res.group(11)or res.group(13) or ''
        self.port = res.group(15)
        self.path = '/' + (res.group(17) or '')
        self.query = res.group(19) or ''
        self.fragment = res.group(21) or ''
        self.res = res

    def _show(self):
        for i in range(len(self.res.groups())):
            print i+1, self.res.group(i+1)

    def gen_url(self, with_password=False):
        """Renders the URL, optionally without the password, based on
        the internal state of it's attributes (hostname, username, etc..)

        >>> u = URLParser('http://www.example.com/path')
        >>> u.
        """
        if not self.scheme:
            raise URLParserError('No scheme specified, please set the `scheme`'
                                 ' attribute')
        s = ['%s://' % self.scheme]
        if self.username:
            u = '[%s]' if set('@:?/#') & set(self.username) else '%s'
            if with_password and self.password:
                u += ':%s' % self.password
            s += ["%s@" % (u % self.username)]
        if self.hostname:
            h = '[%s]' if set(r':?/#') & set(self.hostname) else '%s'
            s += [h % self.hostname]
        if self.port:
            s += [':%s' % self.port]
        if self.path:
            s += [self.path]
        if self.query:
            s += ['?%s' % self.query]
        if self.fragment:
            s += ['#%s' % self.fragment]
        return ''.join(s)

    def __repr__(self):
        return '<URLParser: %s (passwd: %s)>' % (self.gen_url(), self.password)
