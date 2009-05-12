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

from Crypto.PublicKey import ElGamal
from Crypto.Cipher import AES, Blowfish
from Crypto.Util import randpool
from Crypto.Util.number import long_to_bytes, bytes_to_long
from base64 import b64decode, b64encode
import random
from zlib import crc32 # Also available in binascii

#
# Random number generators setup
#
pool = randpool.RandomPool()
pool.stir()
pool.randomize()
randfunc = pool.get_bytes # We'll use this func for most of the random stuff


#
# Encryption errors
#
class DecryptError(Exception):
    """This is raised when we're unable to decrypt a ciphertext or when there
    is an error, such as checksum inconsistencies."""
    def __init__(self, message, attempted=None):
        Exception.__init__(self, message)
        self.attempted = attempted


#
# Checksum padding management
#
def non_zero_crc(txt):
    """Calculate the CRC checksum, ensuring it never ends with \x00,
    thus conflicting with the \x00 padding of encrypted secrets and keys"""
    crc = crc32(txt) & 0xffffffff # Make unsigned hack
    if not crc % 256:
        crc += 1
    return crc

def wrapsum(plainval):
    crc = non_zero_crc(plainval)
    # Add 4 bytes checksum and return
    return plainval + long_to_bytes(crc, 4)

def chksum(sumval):
    # Strip the checksum, and validate:
    crc = sumval[-4:]
    plainval = sumval[:-4]
    cmpcrc = non_zero_crc(plainval)
    
    if (bytes_to_long(crc) != cmpcrc):
        raise DecryptError("Error decrypting: inconsistent cipher: %s" % sumval)

    return plainval

def pad(text, length):
    """Add \x00 characters to pad for multiple of `length`"""
    newtext = (((length - (len(text) % length)) % length) * "\x00")
    return text + newtext


#
# Generate ElGamal keys (for users and groups)
#
def generate_elgamal_keypair():
    """Return an ElGamal object with newly generated keypair"""
    return ElGamal.generate(1536, randfunc)

def elgamal_pubkey(eg):
    """Return only the pubkey from the given ElGamal object"""
    return (eg.p, eg.g, eg.y)

def elgamal_privkey(eg):
    """Return only the privkey from the given ElGamal object"""
    return (eg.p, eg.x)

def elgamal_bothkeys(eg):
    """Return serializable pubkey and privkey from the given ElGamal object"""
    return (eg.p, eg.x, eg.g, eg.y)


#
# Deal with ElGamal pubkey and messages serialization.
#


# _msg are used to store Userciphers in the database (symkey
# encrypted for each user)
def serial_elgamal_msg(cryptsymkey):
    """Get a 2-elements tuple of str(), return a string."""
    try:
        ns = b64encode(cryptsymkey[0]) + ':' + \
             b64encode(cryptsymkey[1])
    except IndexError, e:
        raise DecryptError("Error decrypting: inconsistent message")
    
    return ns

def unserial_elgamal_msg(cryptsymkey):
    """Get a string, return a 2-elements tuple of str()"""
    x = cryptsymkey.split(':')
    try:
        return (b64decode(x[0]),
                b64decode(x[1]))
    except IndexError, e:
        raise DecryptError("Error decrypting: inconsistent message")

# _pubkey are used to encode the public key stored in the database
# (El Gamal pub key, packed together)
def serial_elgamal_pubkey(pubkey):
    """Get a 3-elements tuple of long(), return a string."""
    ns = b64encode(long_to_bytes(pubkey[0])) + ':' + \
         b64encode(long_to_bytes(pubkey[1])) + ':' + \
         b64encode(long_to_bytes(pubkey[2]))         
    return ns

def unserial_elgamal_pubkey(pubkey):
    """Get a string, return a 3-elements tuple of long()"""
    x = pubkey.split(':')
    return (bytes_to_long(b64decode(x[0])),
            bytes_to_long(b64decode(x[1])),
            bytes_to_long(b64decode(x[2])))


# _privkey are used to encode the key in a storable manner
# to go in the ~/.sflvault/config file, as the 'key' key.
# NOTE: privkey ALSO STORES pubkey!
def serial_elgamal_privkey(privkey):
    """Get a 4-elements tuple of long(), return a string.

    This contains the private (two first elements) *and* the public key."""
    ns = b64encode(long_to_bytes(privkey[0])) + ':' + \
         b64encode(long_to_bytes(privkey[1])) + ':' + \
         b64encode(long_to_bytes(privkey[2])) + ':' + \
         b64encode(long_to_bytes(privkey[3]))
    return ns

def unserial_elgamal_privkey(privkey):
    """Get a string, return a 4-elements tuple of long()

    This contains the private (two first elements) and the public key."""
    x = privkey.split(':')
    return (bytes_to_long(b64decode(x[0])),
            bytes_to_long(b64decode(x[1])),
            bytes_to_long(b64decode(x[2])),
            bytes_to_long(b64decode(x[3])))


#
# Encryption / decryption stuff
#

#
# Blowfish encrypt for private keys (client only)
#
def encrypt_privkey(something, pw):
    """Encrypt using a password and Blowfish.

    something should normally be 8-bytes padded, but we add some '\0'
    to pad it.

    Most of the time anyway, we get some base64 stuff to encrypt, so
    it shouldn't pose a problem."""
    b = Blowfish.new(pw)
    nsomething = wrapsum(something)
    nsomething = pad(nsomething, 8)
    return b64encode(b.encrypt(nsomething))

def decrypt_privkey(something, pw):
    """Decrypt using Blowfish and a password

    Remove padding on right."""
    b = Blowfish.new(pw)
    return chksum(b.decrypt(b64decode(something)).rstrip("\x00"))


#
# Encrypt / decrypt service's secrets.
#

def encrypt_secret(secret, seckey=None):
    """Gen. a random key, AES256 encrypts the secret, return the random key"""
    a = None
    if not seckey:
        seckey = randfunc(32)
        a = AES.new(seckey)
    else:
        a = AES.new(b64decode(seckey))

    # Pad with CRC32 checksum
    secret = wrapsum(secret)
    
    # Add padding to have a multiple of 16 bytes
    padded_secret = pad(secret, 16)
    ciphertext = a.encrypt(padded_secret)
    del(padded_secret)
    ciphertext = b64encode(ciphertext)
    seckey = b64encode(seckey)
    del(a)
    return (seckey, ciphertext)

def decrypt_secret(seckey, ciphertext):
    """Decrypt using the provided seckey"""
    a = AES.new(b64decode(seckey))
    ciphertext = b64decode(ciphertext)
    secret = a.decrypt(ciphertext).rstrip("\x00")    
    del(a)
    del(ciphertext)
    # Validate checksum
    return chksum(secret)


#
# Encrypt / decrypt group's privkeys
#
def encrypt_longmsg(eg, message):
    """This takes a long message, and encrypts it as multiple ElGamal-encrypted
    chunks.

    You probably will want to have a serialized message as `message`.

    This will return a b64 version of the encrypted message."""
    # Tested and works to up to 192, but we'll use 96 for safety.
    CHUNK_MAX_SIZE = 96

    message = wrapsum(message)

    # TODO: split into chunks if too long
    ptr = 0
    chunks = []
    while True:
        chunk = message[ptr:ptr+CHUNK_MAX_SIZE]
        if len(chunk):
            chunks.append(chunk)
        if len(chunk) < CHUNK_MAX_SIZE:
            break
        ptr += CHUNK_MAX_SIZE

    out = []
    for chunk in chunks:
        b64chunk = serial_elgamal_msg(eg.encrypt(chunk, randfunc(32)))
        out.append(b64chunk)

    return '&'.join(out)


def decrypt_longmsg(eg, ciphermessage):
    """This takes the long cipher message, splits in chunks and decodes with
    the provided ElGamal key (private key must be in).

    This returns the original str()."""

    chunks = ciphermessage.split('&')
    out = []
    for chunk in chunks:
        snip = eg.decrypt(unserial_elgamal_msg(chunk))
        out.append(snip)

    message = chksum(''.join(out))

    return message
        

# Include the '_' function in the public names
__all__ = [__name for __name in locals().keys() if not __name.startswith('_')]
