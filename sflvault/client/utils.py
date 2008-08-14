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

__all__ = ['shred', 'urlparse', 'AuthenticationError', 'VaultError',
           'VaultIDFormatError', 'VaultConfigurationError', 'RemotingException']



#
# Add protocols to urlparse, for correct parsing of ssh and others.
#
urlparse.uses_netloc.extend(['ssh', 'vlc', 'vpn', 'openvpn', 'git',
                             'bzr+ssh', 'vnc'])


def shred(var):
    """Tries to wipe out from memory certain variables

    Apparently, Python can't do that, or it depends on the implementation.
    We should find a way to do that"""
    l = len(var)
    var = 'x' * l
    return var



### Authentication Exceptions

class AuthenticationError(StandardError):
    def __init__(self, message):
        """Sets an error message"""
        self.message = message
    def __str__(self):
        return self.message


### Vault-communication Exceptions
    
class VaultError(StandardError):
    def __init__(self, message):
        """Sets an error message"""
        self.message = message
    def __str__(self):
        return self.message

class VaultIDFormatError(Exception):
    """When bad parameters are passed to vaultId"""
    pass

class VaultConfigurationError(Exception):
    """Except when we're missing some config info."""
    pass

### Remoting Exceptions

class RemotingException(Exception):
    """When something happens in the Remoting mechanisms"""
    pass
