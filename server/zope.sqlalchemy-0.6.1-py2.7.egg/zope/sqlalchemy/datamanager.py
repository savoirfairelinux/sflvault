##############################################################################
#
# Copyright (c) 2008 Zope Foundation and Contributors.
# All Rights Reserved.
#
# This software is subject to the provisions of the Zope Public License,
# Version 2.1 (ZPL).  A copy of the ZPL should accompany this distribution.
# THIS SOFTWARE IS PROVIDED "AS IS" AND ANY AND ALL EXPRESS OR IMPLIED
# WARRANTIES ARE DISCLAIMED, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF TITLE, MERCHANTABILITY, AGAINST INFRINGEMENT, AND FITNESS
# FOR A PARTICULAR PURPOSE
#
##############################################################################

import transaction as zope_transaction
from zope.interface import implements
from transaction.interfaces import ISavepointDataManager, IDataManagerSavepoint
from transaction._transaction import Status as ZopeStatus
from sqlalchemy.orm.exc import ConcurrentModificationError
from sqlalchemy.exc import DBAPIError
from sqlalchemy.orm.session import SessionExtension
from sqlalchemy.engine.base import Engine

_retryable_errors = []
try:
    import psycopg2.extensions
except ImportError:
    pass
else:
    _retryable_errors.append((psycopg2.extensions.TransactionRollbackError, None))

# ORA-08177: can't serialize access for this transaction
try:
    import cx_Oracle
except ImportError:
    pass
else:
    _retryable_errors.append((cx_Oracle.DatabaseError, lambda e: e.args[0].code==8177))

# The status of the session is stored on the connection info
STATUS_ACTIVE = 'active' # session joined to transaction, writes allowed.
STATUS_CHANGED = 'changed' # data has been written
STATUS_READONLY = 'readonly' # session joined to transaction, no writes allowed.
STATUS_INVALIDATED = STATUS_CHANGED # BBB

NO_SAVEPOINT_SUPPORT = set(['sqlite'])


_SESSION_STATE = {} # a mapping of id(session) -> status
# This is thread safe because you are using scoped sessions


#
# The two variants of the DataManager.
#

class SessionDataManager(object):
    """Integrate a top level sqlalchemy session transaction into a zope transaction
    
    One phase variant.
    """
    
    implements(ISavepointDataManager)

    def __init__(self, session, status, transaction_manager):
        self.transaction_manager = transaction_manager
        self.tx = session.transaction._iterate_parents()[-1]
        self.session = session
        _SESSION_STATE[id(session)] = status
        self.state = 'init'

    def _finish(self, final_state):
        assert self.tx is not None
        session = self.session
        del _SESSION_STATE[id(self.session)]
        self.tx = self.session = None
        self.state = final_state
        # closing the session is the last thing we do. If it fails the
        # transactions don't get wedged and the error propagates
        session.close()

    def abort(self, trans):
        if self.tx is not None: # there may have been no work to do
            self._finish('aborted')

    def tpc_begin(self, trans):
        self.session.flush()
    
    def commit(self, trans):
        status = _SESSION_STATE[id(self.session)]
        if status is not STATUS_INVALIDATED:
            self._finish('no work')

    def tpc_vote(self, trans):
        # for a one phase data manager commit last in tpc_vote
        if self.tx is not None: # there may have been no work to do
            self.tx.commit()
            self._finish('committed')
                
    def tpc_finish(self, trans):
        pass

    def tpc_abort(self, trans):
        assert self.state is not 'committed'

    def sortKey(self):
        # Try to sort last, so that we vote last - we may commit in tpc_vote(),
        # which allows Zope to roll back its transaction if the RDBMS 
        # threw a conflict error.
        return "~sqlalchemy:%d" % id(self.tx)
    
    @property
    def savepoint(self):
        """Savepoints are only supported when all connections support subtransactions
        """

        # ATT: the following check is weak since the savepoint capability 
        # of a RDBMS also depends on its version. E.g. Postgres 7.X does not
        # support savepoints but Postgres is whitelisted independent of its
        # version. Possibly additional version information should be taken
        # into account (ajung)
        if set(engine.url.drivername
               for engine in self.session.transaction._connections.keys()
               if isinstance(engine, Engine)
               ).intersection(NO_SAVEPOINT_SUPPORT):
            raise AttributeError('savepoint')
        return self._savepoint
    
    def _savepoint(self):
        return SessionSavepoint(self.session)
    
    def should_retry(self, error):
        if isinstance(error, ConcurrentModificationError):
            return True
        if isinstance(error, DBAPIError):
            orig = error.orig
            for error_type, test in _retryable_errors:
                if isinstance(orig, error_type):
                    if test is None:
                        return True
                    if test(orig):
                        return True


class TwoPhaseSessionDataManager(SessionDataManager):
    """Two phase variant.
    """
    def tpc_vote(self, trans):
        if self.tx is not None: # there may have been no work to do
            self.tx.prepare()
            self.state = 'voted'
                
    def tpc_finish(self, trans):
        if self.tx is not None:
            self.tx.commit()
            self._finish('committed')

    def tpc_abort(self, trans):
        if self.tx is not None: # we may not have voted, and been aborted already
            self.tx.rollback()
            self._finish('aborted commit')

    def sortKey(self):
        # Sort normally
        return "sqlalchemy.twophase:%d" % id(self.tx)


class SessionSavepoint:
    implements(IDataManagerSavepoint)

    def __init__(self, session):
        self.session = session
        self.transaction = session.begin_nested()

    def rollback(self):
        # no need to check validity, sqlalchemy should raise an exception. I think.
        self.transaction.rollback()


def join_transaction(session, initial_state=STATUS_ACTIVE, transaction_manager=zope_transaction.manager):
    """Join a session to a transaction using the appropriate datamanager.
       
    It is safe to call this multiple times, if the session is already joined
    then it just returns.
       
    `initial_state` is either STATUS_ACTIVE, STATUS_INVALIDATED or STATUS_READONLY
    
    If using the default initial status of STATUS_ACTIVE, you must ensure that
    mark_changed(session) is called when data is written to the database.
    
    The ZopeTransactionExtesion SessionExtension can be used to ensure that this is
    called automatically after session write operations.
    """
    if _SESSION_STATE.get(id(session), None) is None:
        if session.twophase:
            DataManager = TwoPhaseSessionDataManager
        else:
            DataManager = SessionDataManager
        transaction_manager.get().join(DataManager(session, initial_state, transaction_manager))

def mark_changed(session, transaction_manager=zope_transaction.manager):
    """Mark a session as needing to be committed.
    """
    session_id = id(session)
    assert _SESSION_STATE.get(session_id, None) is not STATUS_READONLY, "Session already registered as read only"
    join_transaction(session, STATUS_CHANGED, transaction_manager)
    _SESSION_STATE[session_id] = STATUS_CHANGED


class ZopeTransactionExtension(SessionExtension):
    """Record that a flush has occurred on a session's connection. This allows
    the DataManager to rollback rather than commit on read only transactions.
    """
    
    def __init__(self, initial_state=STATUS_ACTIVE, transaction_manager=zope_transaction.manager):
        if initial_state=='invalidated': initial_state = STATUS_CHANGED #BBB
        SessionExtension.__init__(self)
        self.initial_state = initial_state
        self.transaction_manager = transaction_manager
    
    def after_begin(self, session, transaction, connection):
        join_transaction(session, self.initial_state, self.transaction_manager)
    
    def after_attach(self, session, instance):
        join_transaction(session, self.initial_state, self.transaction_manager)
    
    def after_flush(self, session, flush_context):
        mark_changed(session, self.transaction_manager)
        
    def after_bulk_update(self, session, query, query_context, result):
        mark_changed(session, self.transaction_manager)

    def after_bulk_delete(self, session, query, query_context, result):
        mark_changed(session, self.transaction_manager)
    
    def before_commit(self, session):
        assert self.transaction_manager.get().status == ZopeStatus.COMMITTING, "Transaction must be committed using the transaction manager"
