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

from base64 import b64decode, b64encode
from datetime import datetime
import re

from Crypto.PublicKey import ElGamal
from sqlalchemy import Column, MetaData, Table, types, ForeignKey
from sqlalchemy.orm import mapper, relation, backref
from sqlalchemy.orm import scoped_session, sessionmaker, eagerload, lazyload
from sqlalchemy.orm import eagerload_all
from sqlalchemy.ext.associationproxy import association_proxy
from sqlalchemy import sql

from sflvault.model import meta
from sflvault.model.meta import Session, metadata
from sflvault.model.custom_types import JSONEncodedDict
from sflvault.common.crypto import *


# TODO: add an __all__ statement here, to speed up loading...


def init_model(engine):
    """Call me before using any of the tables or classes in the model."""
    sm = sessionmaker(autoflush=True, transactional=True, bind=engine)

    meta.engine = engine
    meta.Session = scoped_session(sm)



users_table = Table("users", metadata,
                    Column('id', types.Integer, primary_key=True),
                    Column('username', types.Unicode(50)),
                    # ElGamal user's public key.
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
                         Column('is_admin', types.Boolean, default=False),
                         Column('cryptgroupkey', types.Text),
                         )

groups_table = Table('groups', metadata,
                     Column('id', types.Integer, primary_key=True),
                     Column('name', types.Unicode(50)),
                     Column('hidden', types.Boolean, default=False),
                     # ElGamal group's public key
                     Column('pubkey', types.Text),
                     )


servicegroups_table = Table('services_groups', metadata,
                            Column('id', types.Integer, primary_key=True),
                            Column('service_id', types.Integer,
                                   ForeignKey('services.id')),
                            Column('group_id', types.Integer,
                                   ForeignKey('groups.id')),
                            Column('cryptsymkey', types.Text),
                            )


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
                       Column('metadata', JSONEncodedDict), # reserved.
                       Column('notes', types.Text),
                       Column('secret', types.Text),
                       Column('secret_last_modified', types.DateTime)
                       )


class Service(object):
    def __repr__(self):
        return "<Service s#%d: %s>" % (self.id, self.url)

class Machine(object):
    def __repr__(self):
        return "<Machine m#%d: %s (%s %s)>" % (self.id if self.id else 0,
                                               self.name, self.fqdn, self.ip)
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
    """Membership of a user to a group"""
    def __init__(self, user=None):
        if user:
            self.user = user

    def __repr__(self):
        return "<UserGroup element>"

class ServiceGroup(object):
    """membership of a service to a group"""
    def __init__(self, service=None):
        if service:
            self.service = service
        
    def __repr__(self):
        return "<ServiceGroup element>"

class Group(object):
    def __repr__(self):
        return "<Group: %s>" % (self.name)
    
    def elgamal(self):
        """Return the ElGamal object, ready to encrypt stuff."""
        e = ElGamal.ElGamalobj()
        (e.p, e.g, e.y) = unserial_elgamal_pubkey(self.pubkey)
        return e

class Customer(object):
    def __repr__(self):
        return "<Customer c#%d: %s>" % (self.id, self.name)

# User
#  .groups_assoc
#    UserGroup
#     .group
#       Group
#        .services_assoc
#          ServiceGroup
#           .service
#             Service
# Service
#  .groups_assoc
#    ServiceGroup
#     .group
#       Group
#        .users_assoc
#          UserGroup
#           .user
#             User

# Map each class to its corresponding table.
mapper(User, users_table, {
    # Quick access to services...
    'services': relation(Service,
                         secondary=usergroups_table.join(servicegroups_table, usergroups_table.c.group_id==servicegroups_table.c.group_id),
                         backref='users',
                         viewonly=True,
                         ),
    'groups_assoc': relation(UserGroup, backref='user')
    })
User.groups = association_proxy('groups_assoc', 'group')

mapper(UserGroup, usergroups_table, {
    'group': relation(Group, backref='users_assoc')
    })

mapper(Group, groups_table, {
    'services_assoc': relation(ServiceGroup, backref='group')
    })
Group.users = association_proxy('users_assoc', 'user')
Group.services = association_proxy('services_assoc', 'service')

mapper(ServiceGroup, servicegroups_table, {
    'service': relation(Service, backref='groups_assoc')
    })

mapper(Service, services_table, {
    'children': relation(Service,
                         lazy=False,
                         backref=backref('parent', uselist=False,
                                         remote_side=[services_table.c.id]),
                         primaryjoin=services_table.c.parent_service_id==services_table.c.id)
    })
Service.groups = association_proxy('groups_assoc', 'group')

mapper(Machine, machines_table, {
    'services': relation(Service, backref='machine', lazy=False)
    })
mapper(Customer, customers_table, {
    'machines': relation(Machine, backref='customer', lazy=False)
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


def get_objects_ids(objects_ids, object_type):
    """Return a list of valid IDs for certain object types.

    objects_ids - Must be a list of str or ints
    object_type - One of 'groups', 'machines', 'customers
    """
    return get_objects_list(objects_ids, object_type, return_objects=False)[1]


def get_objects_list(objects_ids, object_type, eagerload_all_=None,
                     return_objects=True):
    """Get a list of objects by their IDs, either as int or str. Make
    sure we return a list of integers as IDs.

    object_type - the type of object to be returned. It must be one of
                ['groups', 'machines', 'customers']
    return_objects - whether to return the actual objects or not.
    """

    objects_types_assoc = {'groups': Group,
                           'machines': Machine,
                           'customers': Customer}

    # Check if object_type is valid
    if object_type not in objects_types_assoc:
        raise ValueError("Invalid object type: %s" % (object_type))

    # Get variables
    if isinstance(objects_ids, str):
        objects_ids = [int(objects_ids)]
    elif isinstance(objects_ids, int):
        objects_ids = [objects_ids]
    elif isinstance(objects_ids, list):
        objects_ids = [int(x) for x in objects_ids]
    else:
        raise ValueError("Invalid %s specification" % (object_type))

    # Pull the objects/IDs from the DB
    obj = objects_types_assoc[object_type]
    if return_objects:
        objects_q = query(obj).filter(obj.id.in_(objects_ids))

        if eagerload_all_:
            objects_q = objects_q.options(eagerload_all(eagerload_all_))
        objects = objects_q.all()
    else:
        objects_q = sql.select([obj.id]).where(obj.id.in_(objects_ids))
        objects = meta.Session.execute(objects_q).fetchall()
        
    if len(objects) != len(objects_ids):
        # Woah, you specified objects that didn't exist ?
        valid_objects = [x.id for x in objects]
        invalid_objects = [x for x in objects_ids if x not in valid_objects]
        raise ValueError("Invalid %s: %s" % (object_type, invalid_objects))

    return (objects if return_objects else None, objects_ids)


def search_query(swords, filters=None, verbose=False):

    # Create the join..
    sel = sql.outerjoin(customers_table, machines_table).outerjoin(services_table)

    if filters:
        # Remove filters that are just None
        filters = dict([(x, filters[x]) for x in filters if filters[x]])

        if not isinstance(filters, dict):
            raise RuntimeError("filters param must be a dict, or None")

        if [True for x in filters if not isinstance(filters[x], list)]:
            raise RuntimeError("filters themselves must be a list of ints")
        
        if 'groups' in filters:
            sel = sel.join(servicegroups_table)

    sel = sel.select(use_labels=True)

    if filters:
        if 'groups' in filters:
            sel = sel.where(ServiceGroup.group_id.in_(filters['groups']))
        if 'machines' in filters:
            sel = sel.where(Machine.id.in_(filters['machines']))
        if 'customers' in filters:
            sel = sel.where(Customer.id.in_(filters['customers']))

    # Fields to search in..
    textfields = [Customer.name,
                  Machine.name,
                  Machine.fqdn,
                  Machine.ip,
                  Machine.location,
                  Machine.notes,
                  Service.url,
                  Service.notes]
    numfields = [Customer.id,
                 Machine.id,
                 Service.id]
    
    # TODO: distinguish between INTEGER fields and STRINGS and search
    # differently (check only ==, and only if word can be converted to int())

    andlist = []
    for word in swords:
        orlist = [field.ilike('%%%s%%' % word) for field in textfields]
        if word.isdigit():
            # Search numeric fields too
            orlist += [field == int(word) for field in numfields]
        orword = sql.or_(*orlist)
        andlist.append(orword)

    sel = sel.where(sql.and_(*andlist))

    sel = sel.order_by(Machine.name, Service.url)

    return meta.Session.execute(sel)

