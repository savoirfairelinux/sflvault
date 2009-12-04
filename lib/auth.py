#!/usr/bin/env python
# -*- coding: UTF-8 -*-
#
#    lib/auth.py
#
#    This file is part of SFLvault-QT
#
#    Copyright (C) 2009 Thibault Cohen
#
#    This program is free software; you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation; either version 2 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with this program; if not, write to the Free Software
#    Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307  USA
#
# TODO
# Create subprocess for long processing task (add groups, services ...)


import sys
from PyQt4 import QtCore, QtGui
from sflvault.client import SFLvaultClient

from error import *
token = None

error_message = QtCore.QObject()

mutex = QtCore.QMutex()



def getAuth():
    """
        Get authentication
    """
    global token
    #if not token:
    token = SFLvaultClient()
    mutex.unlock()
    try:
        # Search nothing, just to get a valid token
        mutex.lock()
        status = token.search(["}{[a]"])
        mutex.unlock()
        # If password is bad ...
        if status == False:
            e = Exception("ConnectionDenied")
            e.message = error_message.tr("Connection Denied")
            raise e
    except Exception, e:
        ErrorMessage(e)
        return False
    return token
    
def getUserInfo(username):
    """
        Get Your informations
    """
    global token
    try:
        # get user list, to find you inside ...
        mutex.lock()
        status = token.vault.user_list(token.authtok, True)
        mutex.unlock()
    except xmlrpclib.ProtocolError, e:
        # Protocol error means the token is now invalid
        # So we have to get a new token
        getAuth()
        getUserInfo(username)
    except Exception, e:
        ErrorMessage(e)
        return False
    if status["error"]:
        ErrorMessage("Error while getting your informations")
        return False

    for user in status['list']:
        if user['username'] == username:
            return user
    # Your are not in database ??!!
    return False

def getService(id):
    global token
    try:
        mutex.lock()
        service = token.vault.service.get(token.authtok, id)
        mutex.unlock()
    except xmlrpclib.ProtocolError, e:
        # Protocol error means the token is now invalid
        # So we have to get a new token
        getAuth()
        service = getService(id)
    except Exception, e:
        ErrorMessage(e)
        return False
    if service["error"]:
        ErrorMessage("No service Found")
        return False
    return service

def getMachine(id):
    global token
    try:
        mutex.lock()
        machine = token.vault.machine.get(token.authtok, id)
        mutex.unlock()
    except xmlrpclib.ProtocolError, e:
        # Protocol error means the token is now invalid
        # So we have to get a new token
        getAuth()
        machine = getMachine(id)
    except Exception, e:
        ErrorMessage(e)
        return False
    return machine

def getCustomer(id):
    global token
    try:
        mutex.lock()
        customer = token.vault.customer.get(token.authtok, id)
        mutex.unlock()
    except xmlrpclib.ProtocolError, e:
        # Protocol error means the token is now invalid
        # So we have to get a new token
        getAuth()
        customer = getCustomer(id)
    except Exception, e:
        ErrorMessage(e)
        return False
    return customer

def vaultSearch(pattern, groups_ids=None):
    global token
    result = None
    try:
        mutex.lock()
        result = token.vault.search(token.authtok, pattern, groups_ids)
        mutex.unlock()
    except xmlrpclib.ProtocolError, e:
        # Protocol error means the token is now invalid
        # So we have to get a new token
        getAuth()
        result = vaultSearch(pattern, groups_ids)
    except Exception, e:
        ErrorMessage(e)
        return False
    return result

def getPassword(id):
    global token
    password = None
    try:
        password = token.service_get(id)["plaintext"]
    except Exception, e:
        ErrorMessage(e)
        return False
    return password

def editPassword(id, password):
    global token
    try:
        mutex.lock()
        password = token.vault.service.passwd(token.authtok, id, password)
        mutex.unlock()
    except Exception, e:
        ErrorMessage(e)
        return False
    return password

def listUsers(groups=True):
    global token
    users = None
    try:
        mutex.lock()
        users = token.vault.user_list(token.authtok, groups)["list"]
        mutex.unlock()
    except xmlrpclib.ProtocolError, e:
        # Protocol error means the token is now invalid
        # So we have to get a new token
        getAuth()
        users = listUsers()
    except Exception, e:
        ErrorMessage(e)
        return False
    return users

def addUser(username, admin):
    global token
    try:
        print username
        print admin
        mutex.lock()
        status = token.vault.user.add(token.authtok, username, admin)
        mutex.unlock()
    except xmlrpclib.ProtocolError, e:
        # Protocol error means the token is now invalid
        # So we have to get a new token
        getAuth()
        statusdelUser(username, admin)
    except Exception, e:
        ErrorMessage(e)
        return False
    return status

def delUser(username):
    global token
    try:
        mutex.lock()
        status = token.vault.user_del(token.authtok, username)
        mutex.unlock()
    except xmlrpclib.ProtocolError, e:
        # Protocol error means the token is now invalid
        # So we have to get a new token
        getAuth()
        statusdelUser(username)
    except Exception, e:
        ErrorMessage(e)
        return False
    return status

def listGroup():
    global token
    groups = None
    try:
        mutex.lock()
        status = token.vault.group.list(token.authtok)
        mutex.unlock()
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
        return False
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
        mutex.lock()
        status = token.vault.customer.add(token.authtok, name)
        mutex.unlock()
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
        return False
    return status

def listCustomers():
    try:
        mutex.lock()
        status = token.vault.customer.list(token.authtok)
        mutex.unlock()
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
        return False
    return status

def editCustomer(custid, informations):
    global token
    try:
        mutex.lock()
        status = token.vault.customer.put(token.authtok, custid, informations)
        mutex.unlock()
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
        return False
    return status

def delCustomer(custid):
    global token
    try:
        mutex.lock()
        status = token.vault.customer_del(token.authtok, custid)
        mutex.unlock()
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
        return False
    return status

def addMachine(name, custid, fqdn=None, address=None, location=None, notes=None):
    global token
    try:
        mutex.lock()
        status = token.vault.machine.add(token.authtok, custid, name, fqdn, address, location, notes)
        mutex.unlock()
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
        return False
    return status

def listMachine():
    global token
    try:
        mutex.lock()
        status = token.vault.machine.list(token.authtok)
        mutex.unlock()
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
        return False
    return status

def editMachine(machid, informations):
    global token
    try:
        mutex.lock()
        status = token.vault.machine.put(token.authtok, machid, informations)
        mutex.unlock()
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
        return False
    return status

def delMachine(machid):
    global token
    try:
        mutex.lock()
        status = token.vault.machine_del(token.authtok, machid)
        mutex.unlock()
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
        return False
    return status

def addService(machid, parentid, url, groupids, password, notes):
    global token
    if not parentid:
        parentid = 0
    try:
        if parentid == 0:
            parentif = None
        mutex.lock()
        status = token.vault.service.add(token.authtok, machid, parentid, url, groupids, password, notes)
        mutex.unlock()
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
        return False
    return status

def listService():
    global token
    try:
        mutex.lock()
        status = token.vault.service.list(token.authtok, None)
        mutex.unlock()
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
        return False
    return status

def editService(servid, informations):
    global token
    if not informations["parent_service_id"]:
        informations["parent_service_id"] = 0
    try:
        mutex.lock()
        status = token.vault.service.put(token.authtok, servid, informations)
        mutex.unlock()
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
        return False
    return status

def delService(servid):
    global token
    try:
        mutex.lock()
        status = token.vault.service_del(token.authtok, servid)
        mutex.unlock()
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
        return False
    return status

def addUserGroup(group_id, user, is_admin):
    global token
    from Crypto.PublicKey import ElGamal
    try:
        # TODO: USE this following function
        # status = token.vault.group_add_user(token.authtok, group_id, user, is_admin) 
        # Not is one ...
        mutex.lock()
        token.group_add_user(group_id, user, is_admin)
        mutex.unlock()
        # For now ...
        status = {}
        status["error"] = False
        if status["error"]:
            e = Exception('groupadduser')
            e.message = error_message.tr("Can not add %s user to group g#%d : %s" % (user, group_id, status["message"]))
            raise e
    except xmlrpclib.ProtocolError, e:
        # Protocol error means the token is now invalid
        # So we have to get a new token
        getAuth()
        status = addUserGroup(group_id, user, is_admin)
        if status["error"]:
            e = Exception('groupadduser')
            e.message = error_message.tr("Can not add %s user to group g#%d : %s" % (user, group_id, status["message"]))
            raise e
    except Exception, e:
        ErrorMessage(e)
        return False
    return status

def delUserGroup(group_id, user):
    global token
    try:
        mutex.lock()
        status = token.vault.group_del_user(token.authtok, group_id, user)
        mutex.unlock()
        if status["error"]:
            e = Exception('groupadduser')
            e.message = error_message.tr("Can not delete %s user to group g#%d : %s" % (user, group_id, status["message"]))
            raise e
    except xmlrpclib.ProtocolError, e:
        # Protocol error means the token is now invalid
        # So we have to get a new token
        getAuth()
        status = delUserGroup(group_id, user)
        if status["error"]:
            e = Exception('groupadduser')
            e.message = error_message.tr("Can not delete %s user to group g#%d : %s" % (user, group_id, status["message"]))
            raise e
    except Exception, e:
        ErrorMessage(e)
        return False
    return status

def addGroup(group_name):
    global token
    try:
        mutex.lock()
        status = token.vault.group_add(token.authtok, group_name)
        mutex.unlock()
        if status["error"]:
            e = Exception('groupuser')
            e.message = error_message.tr("Can not create a new group : %s" % (user,group_id))
            raise e
    except xmlrpclib.ProtocolError, e:
        # Protocol error means the token is now invalid
        # So we have to get a new token
        getAuth()
        status = addGroup(group_name)
        if status["error"]:
            e = Exception('groupuser')
            e.message = error_message.tr("Can not create a new group : %s" % (user,group_id))
            raise e
    except Exception, e:
        ErrorMessage(e)
        return False
    return status
