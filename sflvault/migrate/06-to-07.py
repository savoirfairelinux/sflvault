# -=- encoding: utf-8 -=-
# Script to migrate data from version 0.6 to version 0.7
#
# Execute from the root of the project as:
#
#   paster shell
#
# In [1]: %run sflvault/migrate/06-to-07.py
#
# So that all the model and everything is available and initialized.
#

### WARN: make sure you have created the new fields:
#
#usergroups_table (named 'users_groups'):
#  Column('is_admin', types.Boolean, default=False),
#  Column('cryptgroupkey', types.Text),
#
#groups_table (named 'groups'):
#  Column('hidden', types.Boolean, default=False),
#  Column('pubkey', types.Text),
#
#servicegroups_table (named 'services_groups'):
#  Column('cryptsymkey', types.Text),
#

### WARN: Make sure you don't delete the Userciphers table before completion
###       of this upgrade.

### NOTE: This script shouldn't need a running Vault.

from sflvault.client import client
from sflvault import model
from sflvault.lib.common import VaultError
from sflvault.lib.common.crypto import *
from sqlalchemy import sql
from sqlalchemy import Table, Column, types, ForeignKey
from getpass import getpass

try:
    userciphers_table = Table('userciphers', model.meta.metadata,
                          Column('id', types.Integer, primary_key=True),
                          Column('service_id', types.Integer, ForeignKey('services.id')), # relation to services
                          # The user for which this secret is encrypted
                          Column('user_id', types.Integer, ForeignKey('users.id')),
                          # Encrypted symkey with user's pubkey.
                          Column('cryptsymkey', types.Text)
                          )
except Exception, e:
    print "EXCEPTION loading userciphers_table: %s" % e.message


a = client.SFLvaultClient()
myusername = a.cfg.get('SFLvault', 'username')

myuser = model.query(model.User).filter_by(username=myusername).one()


enckey = a.cfg.get('SFLvault', 'key')
passphrase = getpass('Enter your Vault passphrase: ')
packedkey = decrypt_privkey(enckey, passphrase)
eg = ElGamal.ElGamalobj()
(eg.p, eg.x, eg.g, eg.y) = unserial_elgamal_privkey(packedkey)
myeg = eg

# Load all my userciphers for deciphernig later..
userciphers = model.meta.Session.execute(userciphers_table.select().where(userciphers_table.c.user_id==myuser.id))


# Load all groups
allgroups = model.query(model.Group).all()

# Load all users
allusers = model.query(model.User).all()

# This can be done multiple times, but always requires the Userciphers table
# to be present, otherwise, you will lose *everything*.
# Generate keypairs for all groups
for g in allgroups:
    print "Generating keypair for group no %s" % g.id
    
    newkeys = generate_elgamal_keypair()

    g.pubkey = serial_elgamal_pubkey(elgamal_pubkey(newkeys))
    g.keypair = newkeys

    # Loop all users and mod all users
    for usr in allusers:
        for ug in usr.groups_assoc:
            if ug.group_id == g.id:
                ug.is_admin = usr.is_admin
                eg = usr.elgamal()
                ug.cryptgroupkey = encrypt_longmsg(eg, serial_elgamal_privkey(elgamal_bothkeys(newkeys)))
                model.meta.Session.flush()

    # Add to my associations a new association object
    #nug = model.UserGroup()
    #nug.user_id = myuser.id
    #nug.group_id = g.id
    #nug.is_admin = True
    #nug.cryptgroupkey = encrypt_longmsg(myeg, serial_elgamal_privkey(elgamal_bothkeys(newkeys)))
    #myuser.groups_assocs.append(nug)
    model.meta.Session.flush()

#
# 2nd part, decipher all Userciphers I own, and re-encrypt them
# for each group that exists and in which they're part of.
#

#loop des Userciphers
for usercipher in userciphers:
    #load le Service associé.
    # TODO: this expects a consistent database! If service doesn't exist, p00t!
    serv = model.query(model.Service).filter_by(id=usercipher.service_id).one()
    #décryption du symkey du service 
    symkey_plain = myeg.decrypt(unserial_elgamal_msg(usercipher.cryptsymkey))
    #loop des ServiceGroup associés au Service loadé
    for gassoc in serv.groups_assoc:
        # TODO: double check if [0] exists in here.. if the assoc table
        # contains leftovers, this will break.
        #loop des allgroups pour trouver celui-ci.
        grp = [g for g in allgroups if gassoc.group_id == g.id][0]
        #utiliser g.keypair pour encrypter la symkey avec les clés du groupe.
        #remodifier le gassoc avec les bonnes données...
        gassoc.cryptsymkey = encrypt_longmsg(grp.keypair, symkey_plain)
        model.meta.Session.flush()

model.meta.Session.commit()
 
