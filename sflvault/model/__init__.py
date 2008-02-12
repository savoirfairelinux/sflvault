# -=- encoding: utf-8 -=-

from pylons import config
from sqlalchemy import Column, MetaData, Table, types, ForeignKey
from sqlalchemy.orm import mapper, relation
from sqlalchemy.orm import scoped_session, sessionmaker
from datetime import *


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
                    Column('username', types.String(50)),
                    # ElGamal public key.
                    Column('pubkey', types.Text),
                    # This stamp is used to wipe users which haven't 'setup'
                    # their account before this date/time
                    Column('waiting_setup', types.DateTime, nullable=True),
                    Column('created_time', types.DateTime),
                    # Admin flag, allows to add users, and grant access.
                    Column('is_admin', types.Boolean)
                    )

userlevels_table = Table('userlevels', metadata,
                          Column('id', types.Integer, primary_key=True),
                          Column('user_id', types.Integer, ForeignKey('users.id')),
                          Column('level', types.String(50), index=True)
                          )

clients_table = Table('clients', metadata,
                      Column('id', types.Integer, primary_key=True),
                      Column('name', types.String(100)),
                      Column('created_time', types.DateTime),
                      # username, même si yé effacé.
                      Column('created_user', types.String(50))
                      )

servers_table = Table('servers', metadata,
                      Column('id', types.Integer, primary_key=True),
                      Column('client_id', types.Integer, ForeignKey('clients.id')), # relation clients
                      Column('created_time', types.DateTime),
                      # String lisible, un peu de descriptif
                      Column('nom', types.String(150)),
                      # Domaine complet.
                      Column('fqdn', types.String(150)),
                      # Adresse IP si fixe, sinon 'dyn'
                      Column('ip', types.String(100)),
                      # Où il est ce serveur, location géographique, et dans
                      # la ville et dans son boîtier (4ième ?)
                      Column('location', types.Text),
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
        if (self.waiting_setup):
            return False
        elif (datetime.now() < self.waiting_setup):
            return False
        else:
            return True
    
    def __repr__(self):
        return "<User: %s>" % (self.username)

class UserLevel(object):
    def __repr__(self):
        return "<UserLevel: %s>" % (self.level)

class Client(object):
    def __repr__(self):
        return "<Client: %s>" % (self.name)

# Map each class to its corresponding table.
mapper(User, users_table)
mapper(UserLevel, userlevels_table)
mapper(Client, clients_table)
mapper(Server, servers_table)
mapper(Service, services_table)
mapper(Usercipher, userciphers_table)
