***************
zope.sqlalchemy
***************

.. contents::
   :local:

Introduction
============

The aim of this package is to unify the plethora of existing packages
integrating SQLAlchemy with Zope's transaction management. As such it seeks
only to provide a data manager and makes no attempt to define a `zopeish` way
to configure engines.

For WSGI applications, Zope style automatic transaction management is
available with `repoze.tm2`_, a part of `Repoze BFG`_ and `Turbogears 2`_.

You need to understand `SQLAlchemy`_ for this package and this README to make 
any sense.

.. _repoze.tm2: http://docs.repoze.org/tm2/

.. _Repoze BFG: http://bfg.repoze.org/

.. _Turbogears 2: http://turbogears.org/

.. _SQLAlchemy: http://sqlalchemy.org/docs/

Running the tests
=================

This package is distributed as a buildout. Using your desired python run:

$ python bootstrap.py

This will download the dependent packages and setup the test script, which may
be run with:

$ ./bin/test

or with the standard setuptools test command:

$ ./bin/py setup.py test

To enable testing with your own database set the TEST_DSN environment variable
to your sqlalchemy database dsn. Two-phase commit behaviour may be tested by
setting the TEST_TWOPHASE variable to a non empty string. e.g:

$ TEST_DSN=postgres://test:test@localhost/test TEST_TWOPHASE=True bin/test

Example
=======

This example is lifted directly from the SQLAlchemy declarative documentation.
First the necessary imports.

    >>> from sqlalchemy import *
    >>> from sqlalchemy.ext.declarative import declarative_base
    >>> from sqlalchemy.orm import scoped_session, sessionmaker, relation
    >>> from zope.sqlalchemy import ZopeTransactionExtension
    >>> import transaction

Now to define the mapper classes.

    >>> Base = declarative_base()
    >>> class User(Base):
    ...     __tablename__ = 'test_users'
    ...     id = Column('id', Integer, primary_key=True)
    ...     name = Column('name', String(50))
    ...     addresses = relation("Address", backref="user")
    >>> class Address(Base):
    ...     __tablename__ = 'test_addresses'
    ...     id = Column('id', Integer, primary_key=True)
    ...     email = Column('email', String(50))
    ...     user_id = Column('user_id', Integer, ForeignKey('test_users.id'))

Create an engine and setup the tables. Note that for this example to work a 
recent version of sqlite/pysqlite is required. 3.4.0 seems to be sufficient.

    >>> engine = create_engine(TEST_DSN, convert_unicode=True)
    >>> Base.metadata.create_all(engine)

Now to create the session itself. As zope is a threaded web server we must use
scoped sessions. Zope and SQLAlchemy sessions are tied together by using the
ZopeTransactionExtension from this package.

    >>> Session = scoped_session(sessionmaker(bind=engine,
    ... twophase=TEST_TWOPHASE, extension=ZopeTransactionExtension()))

Call the scoped session factory to retrieve a session. You may call this as
many times as you like within a transaction and you will always retrieve the
same session. At present there are no users in the database.

    >>> session = Session()
    >>> session.query(User).all()
    []

We can now create a new user and commit the changes using Zope's transaction
machinary, just as Zope's publisher would.

    >>> session.add(User(id=1, name='bob'))
    >>> transaction.commit()

Engine level connections are outside the scope of the transaction integration.

    >>> engine.connect().execute('SELECT * FROM test_users').fetchall()
    [(1, ...'bob')]

A new transaction requires a new session. Let's add an address.

    >>> session = Session()
    >>> bob = session.query(User).all()[0]
    >>> bob.name
    u'bob'
    >>> bob.addresses
    []
    >>> bob.addresses.append(Address(id=1, email='bob@bob.bob'))
    >>> transaction.commit()
    >>> session = Session()
    >>> bob = session.query(User).all()[0]
    >>> bob.addresses
    [<Address object at ...>]
    >>> bob.addresses[0].email
    u'bob@bob.bob'
    >>> bob.addresses[0].email = 'wrong@wrong'    

To rollback a transaction, use transaction.abort().

    >>> transaction.abort()
    >>> session = Session()
    >>> bob = session.query(User).all()[0]
    >>> bob.addresses[0].email
    u'bob@bob.bob'
    >>> transaction.abort()

By default, zope.sqlalchemy puts sessions in an 'active' state when they are
first used. ORM write operations automatically move the session into a
'changed' state. This avoids unnecessary database commits. Sometimes it
is necessary to interact with the database directly through SQL. It is not
possible to guess whether such an operation is a read or a write. Therefore we
must manually mark the session as changed when manual SQL statements write
to the DB.

    >>> session = Session()
    >>> conn = session.connection()
    >>> users = Base.metadata.tables['test_users']
    >>> conn.execute(users.update(users.c.name=='bob'), name='ben')
    <sqlalchemy.engine.base.ResultProxy object at ...>
    >>> from zope.sqlalchemy import mark_changed
    >>> mark_changed(session)
    >>> transaction.commit()
    >>> session = Session()
    >>> session.query(User).all()[0].name
    u'ben'
    >>> transaction.abort()

If this is a problem you may tell the extension to place the session in the
'changed' state initially.

    >>> Session.configure(extension=ZopeTransactionExtension('changed'))
    >>> Session.remove()
    >>> session = Session()
    >>> conn = session.connection()
    >>> conn.execute(users.update(users.c.name=='ben'), name='bob')
    <sqlalchemy.engine.base.ResultProxy object at ...>
    >>> transaction.commit()
    >>> session = Session()
    >>> session.query(User).all()[0].name
    u'bob'
    >>> transaction.abort()

Development version
===================

`SVN version <svn://svn.zope.org/repos/main/zope.sqlalchemy/trunk#egg=zope.sqlalchemy-dev>`_

