# -=- encoding: utf-8 -=-

from pylons import config
from sqlalchemy import Column, MetaData, Table, types, ForeignKey
from sqlalchemy.orm import mapper, relation
from sqlalchemy.orm import scoped_session, sessionmaker
from datetime import *

from Crypto.PublicKey import ElGamal
from base64 import b64decode, b64encode
import pickle

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
                    Column('created_time', types.DateTime, default=datetime.now()),
                    # Admin flag, allows to add users, and grant access.
                    Column('is_admin', types.Boolean, default=False)
                    )

userlevels_table = Table('userlevels', metadata,
                         Column('id', types.Integer, primary_key=True),
                         Column('user_id', types.Integer, ForeignKey('users.id')),
                         Column('level', types.Unicode(50), index=True)
                         )

customers_table = Table('customers', metadata,
                        Column('id', types.Integer, primary_key=True),
                        Column('name', types.Unicode(100)),
                        Column('created_time', types.DateTime),
                        # username, même si yé effacé.
                        Column('created_user', types.Unicode(50))
                        )

servers_table = Table('servers', metadata,
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
                       Column('server_id', types.Integer, ForeignKey('servers.id')), # relation servers
                       # Type of service, eventually, linked to specific plug-ins.
                       # TODO: ajouter le parent_service_id..
                       Column('type', types.String(50)),
                       Column('port', types.Integer),
                       Column('loginname', types.String(50)),
                       Column('level', types.String(50)),
                       Column('secret', types.Text),
                       # pickled python structures, depends on 'type'
                       Column('metadata', types.Text),
                       Column('notes', types.Text)
                       )

# Table of encrypted symkeys for each 'secret' in the services_table, one for each user.
userciphers_table = Table('userciphers', metadata,
                          Column('id', types.Integer, primary_key=True),
                          Column('service_id', types.Integer, ForeignKey('services.id')), # relation to services
                          # The user for which this secret is encrypted
                          # TODO: check user_id
                          Column('username', types.String(50)),
                          # Encrypted symkey with user's pubkey.
                          Column('stuff', types.Text)
                          )

class Service(object):
    def __repr__(self):
        return "<Service: %s (SRV#%d)>" % (self.name, self.id)

class Server(object):
    def __repr__(self):
        return "<Server: %s (%s)>" % (self.nom, self.fqdn)

class Usercipher(object):
    def __repr__(self):
        return "<Usercipher: %s - service_id: %d>" % (self.username, self.service_id)

class User(object):
    def setup_expired(self):
        """Return True/False if waiting_setup has expired"""
        if (not self.waiting_setup):
            return True
        elif (datetime.now() < self.waiting_setup):
            return False
        else:
            return True

    def elgamal(self):
        """Return the ElGamal object, ready to encrypt stuff."""
        e = ElGamal.ElGamalobj()
        (e.p, e.g, e.y) = pickle.loads(b64decode(self.pubkey))
        return e
    
    def __repr__(self):
        return "<User: %s>" % (self.username)

class UserLevel(object):
    def __repr__(self):
        return "<UserLevel: %s>" % (self.level)

class Customer(object):
    def __repr__(self):
        return "<Customer: %s>" % (self.name)

# Map each class to its corresponding table.
mapper(User, users_table, {
    
    })
mapper(UserLevel, userlevels_table, {
    
    })
mapper(Customer, customers_table, {
    'servers': relation(Server, backref='customer')
    })
mapper(Server, servers_table, {
    
    })
mapper(Service, services_table, {
    })
mapper(Usercipher, userciphers_table, {
    
    })
