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

from pylons import config
from sqlalchemy import Column, MetaData, Table, types, ForeignKey
from sqlalchemy.orm import mapper, relation, backref
from sqlalchemy.orm import scoped_session, sessionmaker, eagerload, lazyload
from sqlalchemy.orm import eagerload_all
from sqlalchemy import sql
from datetime import *

import re

from Crypto.PublicKey import ElGamal
from base64 import b64decode, b64encode

from sflvault.lib.common.crypto import *

# Global session manager.  Session() returns the session object
# appropriate for the current web request.
Session = scoped_session(sessionmaker(autoflush=True, transactional=True,
                                      bind=config['pylons.g'].sa_engine))

mapper = Session.mapper


# Global metadata. If you have multiple databases with overlapping table
# names, you'll need a metadata for each database.
metadata = MetaData()


users_table = Table("users", metadata,
                    Column('id', types.Integer, primary_key=True),
                    Column('username', types.Unicode(50)),
                    # ElGamal public key.
                    Column('pubkey', types.Text),
                    # Used in the login/authenticate challenge
                    Column('logging_token', types.Binary(35)),
                    # Time until the token is valid.
                    Column('logging_timeout', types.DateTime),
                    # This stamp is used to wipe users which haven't 'setup'
                    # their account before this date/time
                    Column('waiting_setup', types.DateTime, nullable=True),
                    Column('created_time', types.DateTime,
                           default=datetime.now()),
                    # Admin flag, allows to add users, and grant access.
                    Column('is_admin', types.Boolean, default=False)
                    )

usergroups_table = Table('users_groups', metadata,
                         Column('id', types.Integer, primary_key=True),
                         Column('user_id', types.Integer,
                                ForeignKey('users.id')),
                         Column('group_id', types.Integer,
                                ForeignKey('groups.id')),
                         )

groups_table = Table('groups', metadata,
                     Column('id', types.Integer, primary_key=True),
                     Column('name', types.Unicode(50)),
                     )
                                
# This is deprecated by usergroups + groups
#userlevels_table = Table('userlevels', metadata,
#                         Column('id', types.Integer, primary_key=True),
#                         Column('user_id', types.Integer,
#                                ForeignKey('users.id')),
#                         Column('level', types.Unicode(50), index=True)
#                         )

customers_table = Table('customers', metadata,
                        Column('id', types.Integer, primary_key=True),
                        Column('name', types.Unicode(100)),
                        Column('created_time', types.DateTime),
                        # username, même si yé effacé.
                        Column('created_user', types.Unicode(50))
                        )

machines_table = Table('machines', metadata,
                      Column('id', types.Integer, primary_key=True),
                      Column('customer_id', types.Integer, ForeignKey('customers.id')), # relation customers
                      Column('created_time', types.DateTime),
                      # Unicode lisible, un peu de descriptif
                      Column('name', types.Unicode(150)),
                      # Domaine complet.
                      Column('fqdn', types.Unicode(150)),
                      # Adresse IP si fixe, sinon 'dyn'
                      Column('ip', types.String(100)),
                      # Où il est ce serveur, location géographique, et dans
                      # la ville et dans son boîtier (4ième ?)
                      Column('location', types.Text),
                      # Notes sur le serveur, références, URLs, etc..
                      Column('notes', types.Text)
                      )

# Each ssh or web app. service that have a password.
services_table = Table('services', metadata,
                       Column('id', types.Integer, primary_key=True),
                       # Service lies on which Machine ?
                       Column('machine_id', types.Integer,
                              ForeignKey('machines.id')),
                       # Hierarchical service required to access this one ?
                       Column('parent_service_id', types.Integer,
                              ForeignKey('services.id')),
                       Column('group_id', types.Integer,
                              ForeignKey('groups.id')),
                       Column('url', types.String(250)), # Full service desc.
                       # simplejson'd python structures, depends on url scheme
                       Column('metadata', types.Text), # reserved.
                       Column('notes', types.Text),
                       Column('secret', types.Text),
                       Column('secret_last_modified', types.DateTime)
                       )

# Table of encrypted symkeys for each 'secret' in the services_table, one for each user.
userciphers_table = Table('userciphers', metadata,
                          Column('id', types.Integer, primary_key=True),
                          Column('service_id', types.Integer, ForeignKey('services.id')), # relation to services
                          # The user for which this secret is encrypted
                          Column('user_id', types.Integer, ForeignKey('users.id')),
                          # Encrypted symkey with user's pubkey.
                          Column('stuff', types.Text)
                          )

class Service(object):
    def __repr__(self):
        return "<Service s#%d: %s>" % (self.id, self.url)

class Machine(object):
    def __repr__(self):
        return "<Machine m#%d: %s (%s %s)>" % (self.id, self.name, self.fqdn, self.ip)

class Usercipher(object):
    def __repr__(self):
        return "<Usercipher: %s - service_id: %d>" % (self.user, self.service_id)

class User(object):
    def setup_expired(self):
        """Return True/False if waiting_setup has expired"""
        if self.waiting_setup and self.waiting_setup < datetime.now():
            return True
        else:
            return False

    def elgamal(self):
        """Return the ElGamal object, ready to encrypt stuff."""
        e = ElGamal.ElGamalobj()
        (e.p, e.g, e.y) = unserial_elgamal_pubkey(self.pubkey)
        return e
    
    def __repr__(self):
        return "<User u#%d: %s>" % (self.id, self.username)

class UserGroup(object):    
    def __repr__(self):
        return "<UserGroup element>"

class Group(object):
    def __repr__(self):
        return "<Group: %s>" % (self.name)
    
# Deprecated by UserGroup + Group
#class UserLevel(object):
#    def __repr__(self):
#        return "<UserLevel: %s>" % (self.level)

class Customer(object):
    def __repr__(self):
        return "<Customer c#%d: %s>" % (self.id, self.name)

# Map each class to its corresponding table.
mapper(User, users_table, {
    'groups': relation(Group, secondary=usergroups_table,
                       backref='users'), # don't eagerload, we'll ask if needed
    'userciphers': relation(Usercipher, backref='user'),
    })

# Not required, the usergroups_table goes through the secondary option
# of mapper(User).. just above..
#
#mapper(UserLevel, userlevels_table, {
#    
#    })

mapper(Group, groups_table, {
    #'userciphers': relation(Usercipher, backref='group'),
    })
mapper(Customer, customers_table, {
    'machines': relation(Machine, backref='customer', lazy=False)
    })
mapper(Machine, machines_table, {
    'services': relation(Service, backref='machine', lazy=False)
    })
mapper(Service, services_table, {
    'children': relation(Service,
                         lazy=False,
                         backref=backref('parent', uselist=False,
                                         remote_side=[services_table.c.id]),
                         primaryjoin=services_table.c.parent_service_id==services_table.c.id),
    'group': relation(Group, backref='services'),
    'userciphers': relation(Usercipher, backref='service'),
    })
mapper(Usercipher, userciphers_table, {
    
    })


################ Helper functions ################


def get_user(user, eagerload_all_=None):
    """Get a user provided a username or an int(user_id), possibly eager
    loading some relations.
    """
    # TODO: DRY
    if isinstance(user, int):
        uq = User.query().filter_by(id=user)
    else:
        uq = User.query().filter_by(username=user)

    if eagerload_all_:
        uq = uq.options(eagerload_all(eagerload_all_))

    usr = uq.first()
    
    if not usr:
        raise LookupError("Invalid user: %s" % user)

    return usr


def get_groups_list(group_ids, eagerload_all_=None):
    """Get a group_ids list, or string, or int, and make sure we
    return a list of integers.
    """
    # Get groups, TODO: DRY
    if isinstance(group_ids, str):
        groupids = [int(group_ids)]
    elif isinstance(group_ids, int):
        groupids = [group_ids]
    elif isinstance(group_ids, list):
        group_ids = [int(x) for x in group_ids]
    else:
        raise ValueError("Invalid groups specification")


    # Pull the groups from the DB
    groups_q = Group.query.filter(Group.id.in_(group_ids))

    if eagerload_all_:
        groups_q = groups_q.options(eagerload_all(eagerload_all_))

    groups = groups_q.all()

    if len(groups) != len(group_ids):
        # Woah, you specified groups that didn't exist ?

        gcopy = group_ids
        for x in groups:
            if x.id in gcopy:
                gcopy.remove(x.id)

        raise ValueError("Invalid group(s): %s" % gcopy)

    return (groups, group_ids)


def search_query(swords, verbose=False):

    # Create the join..
    sel = sql.join(Customer, Machine).join(Service).join(Group) \
                                                   .select(use_labels=True)

    # Fields to search in..
    allfields = [Customer.c.name,
                 Machine.c.name,
                 Machine.c.fqdn,
                 Machine.c.ip,
                 Machine.c.location,
                 Machine.c.notes,
                 Service.c.url,
                 Service.c.notes]

    andlist = []
    for word in swords:
        orlist = [field.ilike('%%%s%%' % word) for field in allfields]
        orword = sql.or_(*orlist)
        andlist.append(orword)

    sel = sel.where(sql.and_(*andlist))

    return Session.execute(sel)
