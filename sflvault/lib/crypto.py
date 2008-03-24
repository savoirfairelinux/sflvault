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

"""Provides function to serialize and unserialize cryptographic blobs"""

from Crypto.Util.number import long_to_bytes, bytes_to_long
from base64 import b64decode, b64encode

#
# Deal with ElGamal pubkey and messages serialization.
#
# TODO: DRY those 6 functions, they are found in sflvault.py
def serial_elgamal_msg(stuff):
    """Get a 2-elements tuple of str(), return a string."""
    ns = b64encode(stuff[0]) + ':' + \
         b64encode(stuff[1])
    return ns

def unserial_elgamal_msg(stuff):
    """Get a string, return a 2-elements tuple of str()"""
    x = stuff.split(':')
    return (b64decode(x[0]),
            b64decode(x[1]))

def serial_elgamal_pubkey(stuff):
    """Get a 3-elements tuple of long(), return a string."""
    ns = b64encode(long_to_bytes(stuff[0])) + ':' + \
         b64encode(long_to_bytes(stuff[1])) + ':' + \
         b64encode(long_to_bytes(stuff[2]))         
    return ns

def unserial_elgamal_pubkey(stuff):
    """Get a string, return a 3-elements tuple of long()"""
    x = stuff.split(':')
    return (bytes_to_long(b64decode(x[0])),
            bytes_to_long(b64decode(x[1])),
            bytes_to_long(b64decode(x[2])))

def serial_elgamal_privkey(stuff):
    """Get a 2-elements tuple of long(), return a string."""
    ns = b64encode(long_to_bytes(stuff[0])) + ':' + \
         b64encode(long_to_bytes(stuff[1]))
    return ns

def unserial_elgamal_privkey(stuff):
    """Get a string, return a 2-elements tuple of long()"""
    x = stuff.split(':')
    return (bytes_to_long(b64decode(x[0])),
            bytes_to_long(b64decode(x[1])))


#
# Encryption / decryption stuff
#

