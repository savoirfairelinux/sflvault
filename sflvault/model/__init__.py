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

from sqlalchemy import Column, MetaData, Table, types, ForeignKey
from sqlalchemy.orm import mapper, relation, backref
from sqlalchemy.orm import scoped_session, sessionmaker, eagerload, lazyload
from sqlalchemy.orm import eagerload_all
from sqlalchemy import sql
from datetime import datetime

from Crypto.PublicKey import ElGamal
from base64 import b64decode, b64encode

from sflvault.model import meta
from sflvault.model.meta import Session, metadata
from sflvault.lib.common.crypto import *

import re


# TODO: add an __all__ statement here, to speed up loading...


def init_model(engine):
    """Call me before using any of the tables or classes in the model."""
    sm = sessionmaker(autoflush=True, transactional=True, bind=engine)

    meta.engine = engine
    meta.Session = scoped_session(sm)



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


servicegroups_table = Table('services_groups', metadata,
                            Column('id', types.Integer, primary_key=True),
                            Column('service_id', types.Integer,
                                   ForeignKey('services.id')),
                            Column('group_id', types.Integer,
                                   ForeignKey('groups.id')),
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
                       # REMOVED: replaced by servicegroups_table many-to-many.
                       #Column('group_id', types.Integer,
                       #       ForeignKey('groups.id')),
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
                          Column('cryptsymkey', types.Text)
                          )

class Service(object):
    def __repr__(self):
        return "<Service s#%d: %s>" % (self.id, self.url)

class Machine(object):
    def __repr__(self):
        return "<Machine m#%d: %s (%s %s)>" % (self.id if self.id else 0,
                                               self.name, self.fqdn, self.ip)

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

# Should never be used, removed temporarily to see if everything works without:
#class UserGroup(object):    
#    def __repr__(self):
#        return "<UserGroup element>"
#class ServiceGroup(object):
#    def __repr__(self):
#        return "<ServiceGroup element>"

class Group(object):
    def __repr__(self):
        return "<Group: %s>" % (self.name)
    
class Customer(object):
    def __repr__(self):
        return "<Customer c#%d: %s>" % (self.id, self.name)

# 2-hops join:
#user_serv_join = sql.join(users_table, usergroups_table)\
#                    .onclause(users_table.c.id == usergroups_table.c.user_id)\
#                    .join(usergroups_table, servicegroups_table)\
#                    .onclause(usergroups_table.c.group_id == servicegroups.c.group_id)\
#                    .join(services_table)\
#                    .onclause(servicegroups_table.c.service_id == services_table.id)

# Map each class to its corresponding table.
mapper(User, users_table, {
    'groups': relation(Group, secondary=usergroups_table,
                       backref='users'), # don't eagerload, we'll ask if needed
    'userciphers': relation(Usercipher, backref='user'),
    'services': relation(Service, viewonly=True,
                         secondary=usergroups_table.join(servicegroups_table, usergroups_table.c.group_id==servicegroups_table.c.group_id),
                         backref='users',
                         viewonly=True,
                         )
    })

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
    'groups': relation(Group, secondary=servicegroups_table,
                       backref='services'),
    'userciphers': relation(Usercipher, backref='service'),
    })
mapper(Usercipher, userciphers_table, {
    
    })


################ Helper functions ################

def query(cls):
    """Shortcut to meta.Session.query(cls)"""
    return meta.Session.query(cls)


def get_user(user, eagerload_all_=None):
    """Get a user provided a username or an int(user_id), possibly eager
    loading some relations.
    """
    if isinstance(user, int):
        uq = query(User).filter_by(id=user)
    else:
        uq = query(User).filter_by(username=user)

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
    # Get groups
    if isinstance(group_ids, str):
        group_ids = [int(group_ids)]
    elif isinstance(group_ids, int):
        group_ids = [group_ids]
    elif isinstance(group_ids, list):
        group_ids = [int(x) for x in group_ids]
    else:
        raise ValueError("Invalid groups specification")


    # Pull the groups from the DB
    groups_q = query(Group).filter(Group.id.in_(group_ids))

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
    sel = sql.join(Customer, Machine).join(Service) \
             .select(use_labels=True)

    # Fields to search in..
    allfields = [Customer.c.id,
                 Customer.c.name,
                 Machine.c.id,
                 Machine.c.name,
                 Machine.c.fqdn,
                 Machine.c.ip,
                 Machine.c.location,
                 Machine.c.notes,
                 Service.c.id,
                 Service.c.url,
                 Service.c.notes]
    
    # TODO: distinguish between INTEGER fields and STRINGS and search
    # differently (check only ==, and only if word can be converted to int())

    andlist = []
    for word in swords:
        orlist = [field.ilike('%%%s%%' % word) for field in allfields]
        orword = sql.or_(*orlist)
        andlist.append(orword)

    sel = sel.where(sql.and_(*andlist))

    return meta.Session.execute(sel)

