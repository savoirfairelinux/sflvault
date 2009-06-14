# -*- coding: UTF-8 -*-

import sys
from PyQt4 import QtCore, QtGui
from sflvault.client import SFLvaultClient

from lib.error import *
token = None

def getAuth():
    """
        Get authentication
    """
    global token
    if not token:
        token = SFLvaultClient()
        try:
            token.search("[a]")
        except Exception, e:
            ErrorMessage(e)
            return None
#        vaultSearch("[a]")
    return token
    
def getService(id):
    global token
    try:
        service = token.vault.service.get(token.authtok, id)
    except Exception, e:
        ErrorMessage(e)
        return None
    return service

def getMachine(id):
    global token
    try:
        machine = token.vault.machine.get(token.authtok, id)
    except Exception, e:
        ErrorMessage(e)
        return None
    return machine

def getCustomer(id):
    global token
    try:
        customer = token.vault.customer.get(token.authtok, id)
    except Exception, e:
        ErrorMessage(e)
        return None
    return customer

def vaultSearch(pattern, groups_ids=None):
    global token
    result = None
    try:
        result = token.vault.search(token.authtok, pattern, groups_ids)
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
        Errormessage(e)
        return None
    return password

def getUserList():
    global token
    users = None
    try:
        users = token.vault.user_list(token.authtok, True)["list"]
    except Exception, e:
        ErrorMessage(e)
        return None
    return users

def getGroupList():
    global token
    groups = None
    try:
        groups = token.vault.group_list(token.authtok)["list"]
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
