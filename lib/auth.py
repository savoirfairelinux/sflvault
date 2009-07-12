# -*- coding: UTF-8 -*-

import sys
from PyQt4 import QtCore, QtGui
from sflvault.client import SFLvaultClient

#from lib.error import *
from error import *
token = None

error_message = QtCore.QObject()

def getAuth():
    """
        Get authentication
    """
    global token
    #if not token:
    token = SFLvaultClient()
    try:
        # Search nothing, just to get a valid token
        status = token.search(["}{[a]"])
        if not status:
            
            e = Exception("ConnectionDenied")
            e.message = error_message.tr("Connection Denied")
            raise e
    except Exception, e:
        ErrorMessage(e)
        return False
    return token
    
def getService(id):
    global token
    try:
        service = token.vault.service.get(token.authtok, id)
    except xmlrpclib.ProtocolError, e:
        # Protocol error means the token is now invalid
        # So we have to get a new token
        getAuth()
        service = getService(id)
    except Exception, e:
        ErrorMessage(e)
        return None
    if service["error"]:
        ErrorMessage("No service Found")
        return None
    return service

def getMachine(id):
    global token
    try:
        machine = token.vault.machine.get(token.authtok, id)
    except xmlrpclib.ProtocolError, e:
        # Protocol error means the token is now invalid
        # So we have to get a new token
        getAuth()
        machine = getMachine(id)
    except Exception, e:
        ErrorMessage(e)
        return None
    return machine

def getCustomer(id):
    global token
    try:
        customer = token.vault.customer.get(token.authtok, id)
    except xmlrpclib.ProtocolError, e:
        # Protocol error means the token is now invalid
        # So we have to get a new token
        getAuth()
        customer = getCustomer(id)
    except Exception, e:
        ErrorMessage(e)
        return None
    return customer

def vaultSearch(pattern, groups_ids=None):
    global token
    result = None
    try:
        result = token.vault.search(token.authtok, pattern, groups_ids)
    except xmlrpclib.ProtocolError, e:
        # Protocol error means the token is now invalid
        # So we have to get a new token
        getAuth()
        result = vaultSearch(pattern, groups_ids)
    except Exception, e:
        ErrorMessage(e)
        return None
    return result

def getPassword(id):
    global token
    password = None
    try:
        password = token.service_get(id)["plaintext"]
    except Exception, e:
        ErrorMessage(e)
        return None
    return password

def getUserList():
    global token
    users = None
    try:
        users = token.vault.user_list(token.authtok, True)["list"]
    except xmlrpclib.ProtocolError, e:
        # Protocol error means the token is now invalid
        # So we have to get a new token
        getAuth()
        users = getUserList()
    except Exception, e:
        ErrorMessage(e)
        return None
    return users

def getGroupList():
    global token
    groups = None
    try:
        groups = token.vault.group_list(token.authtok)["list"]
    except xmlrpclib.ProtocolError, e:
        # Protocol error means the token is now invalid
        # So we have to get a new token
        getAuth()
        groups = getGroupList()
    except Exception, e:
        ErrorMessage(e)
        return None
    return groups


token_alias = SFLvaultClient()

def getAliasList():
    aliases = token_alias.alias_list()
    return aliases

def saveAlias(alias, id):
    token_alias.alias_add(alias,id)

def delAlias(alias):
    token_alias.alias_del(alias)

def getAlias(alias):
    id = token_alias.alias_get(alias)
    return id
