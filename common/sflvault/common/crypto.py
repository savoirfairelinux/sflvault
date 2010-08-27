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
import os
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
    if 'SFLVAULT_IN_TEST' in os.environ:
        print "WARNING: IN TEST MODE, EVERY KEYPAIR GENERATION IS BYPASSED AND USES A PRE-GENERATED AND WORLD-KNOWN KEYPAIR. REMOVE 'SFLVAULT_IN_TEST' FROM YOUR ENVIRONMENT IF YOU ARE DOING THIS ON PRODUCTION"
        eg = ElGamal.ElGamalobj()
        keys = [(177089723724552644256797243527295142469255734138493329314329932362154457094059269514887621456192343485606008571733849784882603220703971587460034382850082611103881050702039214183956206957248098956098183898169452181835193285526486693996807247957663965314452283162788463761928354944430848933147875443419511844733534867714246125293090881680286010834371853006350372947758409794906981881841508329191534306452090259107460058479336274992461969572007575859837L, 2368830913657867259423174096782984007672147302922056255072161233714845396747550413964785336340342087070536608406864241095864284199288769810784864221075742905057068477336098276284927890562488210509136821440679916802167852789973929164278286140181738520594891315446533462206307248550944558426698389577513200698569512147125339722576147002382255876258436727504192479647579172625910816774587488928783787624267035610900290120258307919121453927670441700811482181614216947L, 5861471316007038922650757021308043193803646029154275389954930654765928019938681282006482343772842302607960473277926921384673235972813815577111985557701858831111694263179407993690846841997398288866685890418702914928188654979371728552059661796422031090374692580710906447170464105162673344042938184790777466702148445760745296149876416417949678454708511011740073066144877868339403040477747772225977519821312965207L, 1169412825199936698700035513185825593893938895474876750007859746409857305379860678064015124546593449912724002752383066585681624318254362438491372548721947497497739043831382430104856590871057670575051579668363576657397472353061812950884556034822611307705562237354213497368218843244103113882159981178841442771150519161251285978446459307942619668439466357674240712609844734284943761543870187004331653216116937988266963743961096619840352159665738163357566198583064435L),
                (363126185715790250119395282425017818083421673278440118808474954552806007436370887232958142538070938460903011757636551318850215594111019699633958587914824512339681573953775134121488999147928038505883131989323638021781157246124428000084118138446325126739005521403114471077697023469488488105229388102971903306007555362613775010306064798678761753948810755236011346132218974049446116094394433461746597812371697367173395113014824646850943586174124632464143L, 1989666736598081965365973787349938627625613245335951894925228395719349924579514682166704542464221001327015131231101009506582078440087637470784673000661958376397578391397303146171320274531265903747455382524598808613766406694744319576824028880703970997080651320662468590292703565426391011134523391035995750230341849776175803186815053305823053143914398318121693692044542134832809759905437953710838534372887584358442203447387293183908262967797038874535690090799742911L, 133850088107174975861015682594827971956767368440585898108600141692889215241539178575381178799995195531301157505453120993980045956642227472649664668888717884598815932243844750408878011387532720932159839454554017574665882963054750224693505390054364096154711586190837517112644639757613967217614109546151313073865262488626822109764294618345504453742784825659007630866924661811701179640013729327586347L, 742665583685283032188129474839034185107068199926583417281240975739235100098517297493350864258177674271267050862217567671938790648634008735784684115797768392310253433978502694449565453913758801583487678024491118014887051643096970952295790434950566748516670079663712282848262006606082748685002561868381598918739708181310245226480020229450553192469536632519293406262550081671717685585065331112633947328611250435010734072352883491446355872734313855711051794348490960L)]
        eg.g, eg.p, eg.x, eg.y = keys[random.randint(0, 1)]
        return eg
    # Otherwise, generate, really :)
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
