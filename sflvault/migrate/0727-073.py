# -=- encoding: utf-8 -=-
# Script to migrate data from version 0.7.2.7 to version 0.7.3
#
# Execute from the root of the project as:
#
#   paster shell
#
# In [1]: %run sflvault/migrate/0727-to-073.py
#
# So that all the model and everything is available and initialized.
#

### NOTE: This script shouldn't need a running Vault.

#
# Pseudo-code:
#  - to fix badly used CRC32 checksums, we'll have to re-encode the ciphers
#    and the group-ciphers using the new algorithm (which ensures the CRC32
#    never end with a \x00 byte, allowing the byte array to be padded with
#    \x00 characters without any interference.
#
# - We need to loop *all* services,
# - First, grab all my groupkeys, and decrypt them.
# - Load all the group's pubkeys.
# - Load all `service groups` objects. Test the cryptgroupkey
#   - Fix them if broken, re-encode with new algo.
# - Load all services, and their group objects
#   - Find the first matching one of my decrypted group key.
#   - Decrypt the service, analyze and FIX b

from sflvault.client import client
from sflvault import model
from sflvault.model import query
from sflvault.lib.common import VaultError
from sqlalchemy import sql
from getpass import getpass


#------------ REWORKED CRYPTO LIB - FOR TRANSITION USE ONLY

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
        raise DecryptError("Error decrypting: inconsistent cipher: %s" % sumval,
                           sumval)

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
    
    # Validate checksum
    secret = chksum(secret)
    
    del(a)
    del(ciphertext)
    return secret


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


#-------------- END REWORKED CRYPTO LIB -----------




# Migration code



a = client.SFLvaultClient()
myusername = a.cfg.get('SFLvault', 'username')

myuser = model.query(model.User).filter_by(username=myusername).one()


enckey = a.cfg.get('SFLvault', 'key')
passphrase = getpass('Enter your Vault passphrase: ')
packedkey = decrypt_privkey(enckey, passphrase)
eg = ElGamal.ElGamalobj()
(eg.p, eg.x, eg.g, eg.y) = unserial_elgamal_privkey(packedkey)
myeg = eg

# Load all services
allservices = query(model.Service).all()

# Load all groups
allgroups = query(model.Group).all()

# Load the public keys for groups, required when re-encoding broken ciphers.
allgroups_keys = {}
for grp in allgroups:
    eg = ElGamal.ElGamalobj()
    (eg.p, eg.g, eg.y) = unserial_elgamal_pubkey(grp.pubkey)
    allgroups_keys[grp.id] = eg
    

# Decrypt cryptgroupkey for all my groups
mygroups = myuser.groups_assoc
mygroup_ids = [x.group_id for x in mygroups]
mygroup_keys = {}

for grp in mygroups:
    eg = ElGamal.ElGamalobj()
    (eg.p, eg.x, eg.g, eg.y) = unserial_elgamal_privkey(decrypt_longmsg(myeg,
                                                            grp.cryptgroupkey))
    grp.groupkey = eg
    mygroup_keys[grp.group_id] = grp.groupkey

for srv in allservices:
    # essayer de décrypter le service
    # avec tous ses groupes
    gotit = False
    for grp in srv.groups_assoc:
        if grp.group_id in mygroup_ids:
            # Go on le fait avec ça.
            grpkey = mygroup_keys[grp.group_id]
            try:
                aeskey = decrypt_longmsg(grpkey, grp.cryptsymkey)
            except DecryptError, e:
                print e
                print "It is most probably that you only need to remove the last three characters for this cryptsymkey to be valid. It should only be 44 characters long."
                #aeskey = raw_input("Enter corrected AES cryptsymkey: ")
                aeskey = e.attempted[:44]
                print "USING AESKEY: %s" % aeskey
                print "Re-encrypting for all groups"
                for localgrp in srv.groups_assoc:
                    print " .. group %d" % localgrp.group_id
                    localgrp.cryptsymkey = encrypt_longmsg(allgroups_keys[localgrp.group_id], aeskey)
            #
            # Try to decrypt the secret
            try:
                secret = decrypt_secret(aeskey, srv.secret)
            except DecryptError, e:
                print e
                print "If migrating from an older Vault version, it is possible that the shown password is to be taken literally and was well decrypted."
                #secret = raw_input("Enter corrected secret: ")
                secret = e.attempted
                print "USING PASSWORD: %s" % secret
                srv.secret = encrypt_secret(secret, seckey=aeskey)[1]
            gotit = True
            break
    if not gotit:
        print "WARNING: impossible to check for service %s. You do not have access to any groups to deal with it." % srv
        break
    

model.meta.Session.commit()
