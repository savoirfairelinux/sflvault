#!/usr/bin/env python
# -*- coding: utf-8 -*-
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
import os
from PyQt4 import QtCore, QtGui
from sflvault.client import SFLvaultClient
from sflvault.clientqt.gui.config.config import Config
from error import *
try:
    import keyring
except:
    print "No keyring system supported"

client = None
error_message = QtCore.QObject()

settings = Config()
client_alias = SFLvaultClient(str(settings.fileName()))

def manual_auth():
    password, ok = QtGui.QInputDialog.getText( None,
                                   "SFLvault password",
                                   "Type your SFLvault password",
                                   QtGui.QLineEdit.Password,
                                    )
    return str(password)

def getSecret():
    wallet_setting = str(settings.value("SFLvault/wallet").toString())
    if hasattr(keyring.backend, wallet_setting):
        keyring_backend = getattr(keyring.backend, wallet_setting)()
        secret = keyring_backend.get_password("sflvault", str(settings.fileName()))
        return secret if secret else False
    else:
        return False

def setSecret(wallet_id, password=None):
    settings = Config()
    client = SFLvaultClient(str(settings.fileName()))

    # Disable wallet
    if wallet_id == '0':
        client.cfg.wallet_set(wallet_id, None)
        return True
    # Check if sflvault item exists
    if getSecret() != False:
        question = QtGui.QMessageBox(QtGui.QMessageBox.Question,
                                    "Save password in your wallet",
                                    "This password already exists."
                                    "Do you want to replace it ?",
                                    )
        question.addButton(QtGui.QMessageBox.Save)
        question.addButton(QtGui.QMessageBox.Cancel)
        # Ask to user if he wants to replace old password
        ret = question.exec_()
        if ret == QtGui.QMessageBox.Cancel:
            # Do nothing
            return False
        # Simplify code or keep it simple to understand ?
        else:
            # Replace password
            try:
                return client.cfg.wallet_set(wallet_id, password)
            except Exception, e:
                ErrorMessage(e)
                return False

    else:
        # Save a new password
        try:
            return client.cfg.wallet_set(wallet_id, password)
        except Exception, e:
            ErrorMessage(e)
            return False

def getAuth():
    """
        Get authentication
    """
    global client
    #if not client:
    client = SFLvaultClient(str(settings.fileName()))

    # Check if wallet is disabled
    if client.cfg.wallet_list()[0][4] == True:
        client.getpassfunc = manual_auth

    try:
        # Search nothing, just to get a valid client
        status = client.search(["}{[a]"])
        # If password is bad ...
        if status == False:
            e = Exception("ConnectionDenied")
            e.message = error_message.tr("Connection Denied")
            raise e
    except Exception, e:
        ErrorMessage(e)
        return False
    return client
 
def registerAccount(username, vaultaddress, password):
    """ Init you vault account
    """
    client = SFLvaultClient(str(settings.fileName()))
    try:
        client.user_setup(username, vaultaddress, password)
    except Exception, e:
        ErrorMessage(e)
        return False
    return True 

def getUserInfo(username):
    """ Get Your informations
    """
    global client
    try:
        # get user list, to find you inside ...
        status = client.vault.user_list(client.authtok, True)
    except xmlrpclib.ProtocolError, e:
        # Protocol error means the client is now invalid
        # So we have to get a new client
        getAuth()
        getUserInfo(username)
    except Exception, e:
        ErrorMessage(e)
        return False
    try:
        if status["error"]:
            e = Exception('userinfo')
            e.message = error_message.tr("Error while getting your informations")
            ErrorMessage(e)
            return False

        for user in status['list']:
            if user['username'] == username:
                return user
    except UnboundLocalError:
        user = getUserInfo(username)
        return user
    # Your are not in database ??!!
    return False

def getService(id, groups=False):
    global client
    try:
        service = client.vault.service_get_tree(client.authtok, id, groups)
    except xmlrpclib.ProtocolError, e:
        # Protocol error means the client is now invalid
        # So we have to get a new client
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
    global client
    try:
        machine = client.vault.machine.get(client.authtok, id)
    except xmlrpclib.ProtocolError, e:
        # Protocol error means the client is now invalid
        # So we have to get a new client
        getAuth()
        machine = getMachine(id)
    except Exception, e:
        ErrorMessage(e)
        return False
    return machine

def getCustomer(id):
    global client
    try:
        customer = client.vault.customer.get(client.authtok, id)
    except xmlrpclib.ProtocolError, e:
        # Protocol error means the client is now invalid
        # So we have to get a new client
        getAuth()
        customer = getCustomer(id)
    except Exception, e:
        ErrorMessage(e)
        return False
    return customer

def vaultSearch(pattern, filters={}):
    global client
    result = None
    try:
        result = client.vault.search(client.authtok, pattern,
                                filters.get('groups'), False, filters)
    except xmlrpclib.ProtocolError, e:
        # Protocol error means the client is now invalid
        # So we have to get a new client
        getAuth()
        result = vaultSearch(pattern, filters)
    except Exception, e:
        ErrorMessage(e)
        return False
    return result

def getPassword(id):
    global client
    password = None
    try:
        password = client.service_get(id)["plaintext"]
    except Exception, e:
        ErrorMessage(e)
        return False
    return password

def editPassword(id, password):
    global client
    try:
        password = client.vault.service.passwd(client.authtok, id, password)
    except Exception, e:
        ErrorMessage(e)
        return False
    return password

def listUsers(groups=True):
    global client
    users = None
    try:
        users = client.vault.user_list(client.authtok, groups)["list"]
    except xmlrpclib.ProtocolError, e:
        # Protocol error means the client is now invalid
        # So we have to get a new client
        getAuth()
        users = listUsers()
    except Exception, e:
        ErrorMessage(e)
        return False
    return users

def addUser(username, admin):
    global client
    try:
        status = client.vault.user.add(client.authtok, username, admin)
    except xmlrpclib.ProtocolError, e:
        # Protocol error means the client is now invalid
        # So we have to get a new client
        getAuth()
        status = addUser(username, admin)
    except Exception, e:
        ErrorMessage(e)
        return False
    return status

def delUser(username):
    global client
    try:
        status = client.vault.user_del(client.authtok, username)
    except xmlrpclib.ProtocolError, e:
        # Protocol error means the client is now invalid
        # So we have to get a new client
        getAuth()
        status = delUser(username)
    except Exception, e:
        ErrorMessage(e)
        return False
    return status

def listGroup():
    global client
    groups = None
    try:
        status = client.vault.group.list(client.authtok)
        if status["error"]:
            e = Exception('listgroup')
            e.message = error_message.tr("Can not list groups")
            raise e
    except xmlrpclib.ProtocolError, e:
        # Protocol error means the client is now invalid
        # So we have to get a new client
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


def getAliasList():
    aliases = client_alias.cfg.alias_list()
    return aliases

def saveAlias(alias, id):
    client_alias.cfg.alias_add(alias,id)

def delAlias(alias):
    client_alias.cfg.alias_del(alias)

def getAlias(alias):
    id = client_alias.cfg.alias_get(alias)
    return id

def addCustomer(name):
    global client
    try:
        status = client.vault.customer.add(client.authtok, name)
        if status["error"]:
            e = Exception('addcustomer')
            e.message = error_message.tr("Can not add customer : %s" % name)
            raise e
    except xmlrpclib.ProtocolError, e:
        # Protocol error means the client is now invalid
        # So we have to get a new client
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
        status = client.vault.customer.list(client.authtok)
        if status["error"]:
            e = Exception('listcustomer')
            e.message = error_message.tr("Can not list customers")
            raise e
    except xmlrpclib.ProtocolError, e:
        # Protocol error means the client is now invalid
        # So we have to get a new client
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
    global client
    try:
        status = client.vault.customer.put(client.authtok, custid, informations)
        if status["error"]:
            e = Exception('editcustomer')
            e.message = error_message.tr("Can not edit customer : %s" % informations["name"])
            raise e
    except xmlrpclib.ProtocolError, e:
        # Protocol error means the client is now invalid
        # So we have to get a new client
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
    global client
    try:
        status = client.vault.customer_del(client.authtok, custid)
        if status["error"]:
            e = Exception('delcustomer')
            e.message = error_message.tr("Can not delete customer : %s" % custid)
            raise e
    except xmlrpclib.ProtocolError, e:
        # Protocol error means the client is now invalid
        # So we have to get a new client
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
    global client
    try:
        status = client.vault.machine.add(client.authtok, custid, name, fqdn, address, location, notes)
        if status["error"]:
            e = Exception('addmachine')
            e.message = error_message.tr("Can not add machine : %s" % name)
            raise e
    except xmlrpclib.ProtocolError, e:
        # Protocol error means the client is now invalid
        # So we have to get a new client
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
    global client
    try:
        status = client.vault.machine_list(client.authtok)
        if status["error"]:
            e = Exception('listmachine')
            e.message = error_message.tr("Can not list machines")
            raise e
    except xmlrpclib.ProtocolError, e:
        # Protocol error means the client is now invalid
        # So we have to get a new client
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
    global client
    try:
        status = client.vault.machine.put(client.authtok, machid, informations)
        if status["error"]:
            e = Exception('editmachine')
            e.message = error_message.tr("Can not edit machine : %s" % informations["name"])
            raise e
    except xmlrpclib.ProtocolError, e:
        # Protocol error means the client is now invalid
        # So we have to get a new client
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
    global client
    try:
        status = client.vault.machine_del(client.authtok, machid)
        if status["error"]:
            e = Exception('delmachine')
            e.message = error_message.tr("Can not delete machine : %s" % machid)
            raise e
    except xmlrpclib.ProtocolError, e:
        # Protocol error means the client is now invalid
        # So we have to get a new client
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
    global client
    if not parentid:
        parentid = 0
    try:
        if parentid == 0:
            parentif = None
        status = client.vault.service.add(client.authtok, machid, parentid, url, groupids, password, notes)
        if status["error"]:
            e = Exception('addservice')
            e.message = error_message.tr("Can not add service : %s" % url)
            raise e
    except xmlrpclib.ProtocolError, e:
        # Protocol error means the client is now invalid
        # So we have to get a new client
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
    global client
    try:
        status = client.vault.service.list(client.authtok, None)
        if status["error"]:
            e = Exception('listservice')
            # FIXME
            # Print message from vault... but can t be translate ...
            #e.message = status["message"]
            e.message = error_message.tr("Can not list services")
            raise e
    except xmlrpclib.ProtocolError, e:
        # Protocol error means the client is now invalid
        # So we have to get a new client
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
    global client
    if not informations["parent_service_id"]:
        informations["parent_service_id"] = 0
    try:
        status = client.vault.service.put(client.authtok, servid, informations)
        if status["error"]:
            e = Exception('editservice')
            e.message = error_message.tr("Can not edit service : %s" % informations["url"])
            raise e
    except xmlrpclib.ProtocolError, e:
        # Protocol error means the client is now invalid
        # So we have to get a new client
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
    global client
    try:
        status = client.vault.service_del(client.authtok, servid)
        if status["error"]:
            e = Exception('delservice')
            e.message = error_message.tr("Can not delete service : %s" % servid)
            raise e
    except xmlrpclib.ProtocolError, e:
        # Protocol error means the client is now invalid
        # So we have to get a new client
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
    global client
    from Crypto.PublicKey import ElGamal
    try:
        # TODO: USE this following function
        # status = client.vault.group_add_user(client.authtok, group_id, user, is_admin) 
        # Not is one ...
        client.group_add_user(group_id, user, is_admin)
        # For now ...
        status = {}
        status["error"] = False
        if status["error"]:
            e = Exception('groupadduser')
            e.message = error_message.tr("Can not add %s user to group g#%d : %s" % (user, group_id, status["message"]))
            raise e
    except xmlrpclib.ProtocolError, e:
        # Protocol error means the client is now invalid
        # So we have to get a new client
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
    global client
    try:
        status = client.vault.group_del_user(client.authtok, group_id, user)
        if status["error"]:
            e = Exception('groupdeluser')
            e.message = error_message.tr("Can not delete %s user to group g#%d : %s" % (user, group_id, status["message"]))
            raise e
    except xmlrpclib.ProtocolError, e:
        # Protocol error means the client is now invalid
        # So we have to get a new client
        getAuth()
        status = delUserGroup(group_id, user)
        if status["error"]:
            e = Exception('groupdeluser')
            e.message = error_message.tr("Can not delete %s user to group g#%d : %s" % (user, group_id, status["message"]))
            raise e
    except Exception, e:
        ErrorMessage(e)
        return False
    return status

def addGroup(group_name):
    global client
    try:
        status = client.vault.group_add(client.authtok, group_name)
        print status
        if status["error"]:
            e = Exception('groupadd')
            e.message = error_message.tr("Can not create a new group : %s" % (user,group_id))
            raise e
    except xmlrpclib.ProtocolError, e:
        # Protocol error means the client is now invalid
        # So we have to get a new client
        getAuth()
        status = addGroup(group_name)
        if status["error"]:
            e = Exception('groupadd')
            e.message = error_message.tr("Can not create a new group : %s" % (user,group_id))
            raise e
    except Exception, e:
        ErrorMessage(e)
        return False
    return status

def delGroup(group_id):
    global client
    try:
        status = client.vault.group_del(client.authtok, group_id)
        if status["error"]:
            e = Exception('groupdel')
            e.message = error_message.tr("Can not delete group : %s" % (user,group_id))
            raise e
    except xmlrpclib.ProtocolError, e:
        # Protocol error means the client is now invalid
        # So we have to get a new client
        getAuth()
        status = delGroup(group_id)
        if status["error"]:
            e = Exception('groupdel')
            e.message = error_message.tr("Can not delete group : %s" % (user,group_id))
            raise e
    except Exception, e:
        ErrorMessage(e)
        return False
    return status

def addServiceGroup(group_id, service_id):
    global client
    from Crypto.PublicKey import ElGamal
    try:
        # TODO: USE this following function
        # status = client.vault.group_add_service(client.authtok, group_id, service_id)
        # Not is one ...
        client.group_add_service(group_id, service_id)
        # For now ...
        status = {}
        status["error"] = False
        if status["error"]:
            e = Exception('groupaddservice')
            e.message = error_message.tr("Can not add service s#%s to group g#%d : %s" % (service_id, group_id, status["message"]))
            raise e
    except xmlrpclib.ProtocolError, e:
        # Protocol error means the client is now invalid
        # So we have to get a new client
        getAuth()
        status = addServiceGroup(group_id, service_id)
        if status["error"]:
            e = Exception('groupaddservice')
            e.message = error_message.tr("Can not add service s#%s to group g#%d : %s" % (service_id, group_id, status["message"]))
            raise e
    except Exception, e:
        ErrorMessage(e)
        return False
    return status

def delServiceGroup(group_id, service_id):
    global client
    try:
        status = client.vault.group_del_service(client.authtok, group_id, service_id)
        if status["error"]:
            e = Exception('groupdelservice')
            e.message = error_message.tr("Can not delete service #%s to group g#%d : %s" % (service_id, group_id, status["message"]))
            raise e
    except xmlrpclib.ProtocolError, e:
        # Protocol error means the client is now invalid
        # So we have to get a new client
        getAuth()
        status = delServiceGroup(group_id, service_id)
        if status["error"]:
            e = Exception('groupdelservice')
            e.message = error_message.tr("Can not delete service #%s to group g#%d : %s" % (service_id, group_id, status["message"]))
            raise e
    except Exception, e:
        ErrorMessage(e)
        return False
    return status
