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
        # If password is bad ...
        if status == False:
            e = Exception("ConnectionDenied")
            e.message = error_message.tr("Connection Denied")
            raise e
    except Exception, e:
        ErrorMessage(e)
        return None
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
        print "machine" 
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

def editPassword(id, password):
    global token
    try:
        password = token.vault.service.passwd(token.authtok, id, password)
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

def listGroup():
    global token
    groups = None
    try:
        status = token.vault.group.list(token.authtok)
        if status["error"]:
            e = Exception('listgroup')
            e.message = error_message.tr("Can not list groups")
            raise e
    except xmlrpclib.ProtocolError, e:
        # Protocol error means the token is now invalid
        # So we have to get a new token
        getAuth()
        status = listGroup()
        if status["error"]:
            e = Exception('listgroup')
            e.message = error_message.tr("Can not list groups")
            raise e
    except Exception, e:
        ErrorMessage(e)
        return None
    return status

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

def addCustomer(name):
    global token
    try:
        status = token.vault.customer.add(token.authtok, name)
        if status["error"]:
            e = Exception('addcustomer')
            e.message = error_message.tr("Can not add customer : %s" % name)
            raise e
    except xmlrpclib.ProtocolError, e:
        # Protocol error means the token is now invalid
        # So we have to get a new token
        getAuth()
        status = addCustomer(name)
        if status["error"]:
            e = Exception('addcustomer')
            e.message = error_message.tr("Can not add customer : %s" % name)
            raise e
    except Exception, e:
        ErrorMessage(e)
        return None
    return status

def listCustomers():
    try:
        status = token.vault.customer.list(token.authtok)
        if status["error"]:
            e = Exception('listcustomer')
            e.message = error_message.tr("Can not list customers")
            raise e
    except xmlrpclib.ProtocolError, e:
        # Protocol error means the token is now invalid
        # So we have to get a new token
        getAuth()
        status = listCustomers()
        if status["error"]:
            e = Exception('listcustomer')
            e.message = error_message.tr("Can not list customers")
            raise e
    except Exception, e:
        ErrorMessage(e)
        return None
    return status

def editCustomer(custid, informations):
    global token
    try:
        status = token.vault.customer.put(token.authtok, custid, informations)
        if status["error"]:
            e = Exception('editcustomer')
            e.message = error_message.tr("Can not edit customer : %s" % informations["name"])
            raise e
    except xmlrpclib.ProtocolError, e:
        # Protocol error means the token is now invalid
        # So we have to get a new token
        getAuth()
        status = editCustomer(custid, informations)
        if status["error"]:
            e = Exception('editcustomer')
            e.message = error_message.tr("Can not edit customer : %s" % informations["name"])
            raise e
    except Exception, e:
        ErrorMessage(e)
        return None
    return status

def delCustomer(custid):
    global token
    try:
        status = token.vault.customer_del(token.authtok, custid)
        if status["error"]:
            e = Exception('delcustomer')
            e.message = error_message.tr("Can not delete customer : %s" % custid)
            raise e
    except xmlrpclib.ProtocolError, e:
        # Protocol error means the token is now invalid
        # So we have to get a new token
        getAuth()
        status = delCustomer(custid)
        if status["error"]:
            e = Exception('delcustomer')
            e.message = error_message.tr("Can not delete customer : %s" % custid)
            raise e
    except Exception, e:
        ErrorMessage(e)
        return None
    return status

def addMachine(name, custid, fqdn=None, address=None, location=None, notes=None):
    global token
    try:
        status = token.vault.machine.add(token.authtok, custid, name, fqdn, address, location, notes)
        if status["error"]:
            e = Exception('addmachine')
            e.message = error_message.tr("Can not add machine : %s" % name)
            raise e
    except xmlrpclib.ProtocolError, e:
        # Protocol error means the token is now invalid
        # So we have to get a new token
        getAuth()
        status = addMachine(name, custid, fqdn=None, address=None, location=None, notes=None)
        if status["error"]:
            e = Exception('addmachine')
            e.message = error_message.tr("Can not add machine : %s" % name)
            raise e
    except Exception, e:
        ErrorMessage(e)
        return None
    return status

def listMachine():
    global token
    try:
        status = token.vault.machine.list(token.authtok)
        if status["error"]:
            e = Exception('listmachine')
            e.message = error_message.tr("Can not list machines")
            raise e
    except xmlrpclib.ProtocolError, e:
        # Protocol error means the token is now invalid
        # So we have to get a new token
        getAuth()
        status = listMachine()
        if status["error"]:
            e = Exception('listmachine')
            e.message = error_message.tr("Can not list machines")
            raise e
    except Exception, e:
        ErrorMessage(e)
        return None
    return status

def editMachine(machid, informations):
    global token
    try:
        status = token.vault.machine.put(token.authtok, machid, informations)
        if status["error"]:
            e = Exception('editmachine')
            e.message = error_message.tr("Can not edit machine : %s" % informations["name"])
            raise e
    except xmlrpclib.ProtocolError, e:
        # Protocol error means the token is now invalid
        # So we have to get a new token
        getAuth()
        status = editMachine(machid, informations)
        if status["error"]:
            e = Exception('editmachine')
            e.message = error_message.tr("Can not edit machine : %s" % informations["name"])
            raise e
    except Exception, e:
        ErrorMessage(e)
        return None
    return status

def delMachine(machid):
    global token
    try:
        status = token.vault.machine_del(token.authtok, machid)
        if status["error"]:
            e = Exception('delmachine')
            e.message = error_message.tr("Can not delete machine : %s" % machid)
            raise e
    except xmlrpclib.ProtocolError, e:
        # Protocol error means the token is now invalid
        # So we have to get a new token
        getAuth()
        status = delMachine(machid)
        if status["error"]:
            e = Exception('delmachine')
            e.message = error_message.tr("Can not delete machine : %s" % machid)
            raise e
    except Exception, e:
        ErrorMessage(e)
        return None
    return status

def addService(machid, parentid, url, groupids, password, notes):
    global token
    if not parentid:
        parentid = 0
    try:
        if parentid == 0:
            parentif = None
        status = token.vault.service.add(token.authtok, machid, parentid, url, groupids, password, notes)
        if status["error"]:
            e = Exception('addservice')
            e.message = error_message.tr("Can not add service : %s" % url)
            raise e
    except xmlrpclib.ProtocolError, e:
        # Protocol error means the token is now invalid
        # So we have to get a new token
        getAuth()
        status = addService(machid, parentid, url, groupids, password, notes)
        if status["error"]:
            e = Exception('addservice')
            e.message = error_message.tr("Can not add service : %s" % url)
            raise e
    except Exception, e:
        ErrorMessage(e)
        return None
    return status

def listService():
    global token
    try:
        status = token.vault.service.list(token.authtok, None)
        if status["error"]:
            e = Exception('listservice')
            # FIXME
            # Print message from vault... but can t be translate ...
            #e.message = status["message"]
            e.message = error_message.tr("Can not list services")
            raise e
    except xmlrpclib.ProtocolError, e:
        # Protocol error means the token is now invalid
        # So we have to get a new token
        getAuth()
        status = listService()
        if status["error"]:
            e = Exception('listservice')
            e.message = error_message.tr("Can not list services")
            raise e
    except Exception, e:
        ErrorMessage(e)
        return None
    return status

def editService(servid, informations):
    global token
    if not informations["parent_service_id"]:
        informations["parent_service_id"] = 0
    try:
        status = token.vault.service.put(token.authtok, servid, informations)
        if status["error"]:
            e = Exception('editservice')
            e.message = error_message.tr("Can not edit service : %s" % informations["url"])
            raise e
    except xmlrpclib.ProtocolError, e:
        # Protocol error means the token is now invalid
        # So we have to get a new token
        getAuth()
        status = editService(servid, informations)
        if status["error"]:
            e = Exception('editservice')
            e.message = error_message.tr("Can not edit service : %s" % informations["url"])
            raise e
    except Exception, e:
        ErrorMessage(e)
        return None
    return status

def delService(servid):
    global token
    try:
        status = token.vault.service_del(token.authtok, servid)
        if status["error"]:
            e = Exception('delservice')
            e.message = error_message.tr("Can not delete service : %s" % servid)
            raise e
    except xmlrpclib.ProtocolError, e:
        # Protocol error means the token is now invalid
        # So we have to get a new token
        getAuth()
        status = delService(servid)
        if status["error"]:
            e = Exception('delservice')
            e.message = error_message.tr("Can not delete service : %s" % servid)
            raise e
    except Exception, e:
        ErrorMessage(e)
        return None
    return status
