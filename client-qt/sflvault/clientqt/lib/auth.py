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
from Crypto.PublicKey import ElGamal

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

def try_connect(func):
    """ Decorator to try to connect to sflvault server
    """
    def try_func(*k,**a):
        try:
            status = func(*k, **a)
        except socket.error, e:
            ErrorMessage(e)
            return False
        return status
    return try_func

def reauth(func):
    """ Decorator to reactivate the client if is expired
    """
    def reauth_func(*k, **a):
        status = func(*k, **a)
        if 'error' in status and status["error"]:
            if status['message'] == 'Permission denied':
                getAuth()
                status = func(*k, **a)
            else:
                ErrorMessage(status['message'])
        return status
    return reauth_func

class return_element(object):
    """ Decorator to get a specified element of the "status" response
        of the vault
    """
    def __init__(self, element):
        self.element = element

    def __call__(self, func):
        def return_el(*k, **a):
            status = func(*k, **a)
            if isinstance(status, dict):
                if self.element in status:
                    status = status[self.element]
                elif self.element == 'plaintext':
                    ErrorMessage("Access denied")
                    return False
            return status
        return return_el

def return_user(func):
    """ Decorator to return current user info
    """
    def ret_user(*k, **a):
        status = func(*k, **a)
        if 'list' in status:
            for user in status['list']:
                if user['username'] == k[0]:
                    return user
        return False
    return ret_user

@return_user
@try_connect
@reauth
def getUserInfo(username):
    """ Get Your informations
    """
    global client
    status = client.vault.user_list(client.authtok, True)
#        for user in status['list']:
#            if user['username'] == username:
#                return user
#    except UnboundLocalError:
#        user = getUserInfo(username)
#        return user
    # Your are not in database ??!!
    return status

@try_connect
@reauth
def getService(id, groups=False):
    global client
    status = client.vault.service_get_tree(client.authtok, id, groups)
    return status

@try_connect
@reauth
def getMachine(id):
    status = client.vault.machine.get(client.authtok, id)
    return status

@try_connect
@reauth
def getCustomer(id):
    global client
    status = client.vault.customer.get(client.authtok, id)
    return status

@try_connect
@reauth
def vaultSearch(pattern, filters={}):
    global client
    result = client.vault.search(client.authtok, pattern,
                                filters.get('groups'), False, filters)
    return result

@return_element("plaintext")
@try_connect
@reauth
def getPassword(id):
    # Can not use client.vault
    # TODO ???
    global client
    status = client.service_get(id)
    return status

@try_connect
@reauth
def editPassword(id, password):
    global client
    status = client.vault.service.passwd(client.authtok, id, password)
    return status

@return_element("list")
@try_connect
@reauth
def listUsers(groups=True):
    global client
    status = client.vault.user_list(client.authtok, groups)
    return status

@try_connect
@reauth
def addUser(username, admin):
    global client
    status = client.vault.user.add(client.authtok, username, admin)
    return status

@try_connect
@reauth
def delUser(username):
    global client
    status = client.vault.user_del(client.authtok, username)
    return status

@try_connect
@reauth
def listGroup():
    global client
    status = client.vault.group.list(client.authtok)
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

@try_connect
@reauth
def addCustomer(name):
    global client
    status = client.vault.customer.add(client.authtok, name)
    return status

@try_connect
@reauth
def listCustomers():
    global client
    status = client.vault.customer_list(client.authtok)
    return status

@try_connect
@reauth
def editCustomer(custid, informations):
    global client
    status = client.vault.customer.put(client.authtok, custid, informations)
    return status

@try_connect
@reauth
def delCustomer(custid):
    global client
    status = client.vault.customer_del(client.authtok, custid)
    return status

@try_connect
@reauth
def addMachine(name, custid, fqdn=None, address=None, location=None, notes=None):
    global client
    status = client.vault.machine.add(client.authtok, custid, name, fqdn, address, location, notes)
    return status

@try_connect
@reauth
def listMachine():
    global client
    status = client.vault.machine_list(client.authtok)
    return status

@try_connect
@reauth
def editMachine(machid, informations):
    global client
    status = client.vault.machine.put(client.authtok, machid, informations)
    return status

@try_connect
@reauth
def delMachine(machid):
    global client
    status = client.vault.machine_del(client.authtok, machid)
    return status

@try_connect
@reauth
def addService(machid, parentid, url, groupids, password, notes, metadata):
    # TODO: put parentid to 0 by default
    global client
    if not parentid:
        parentid = 0
    status = client.vault.service.add(client.authtok, machid, parentid, url,
                                        groupids, password, notes, metadata)
    return status

@try_connect
@reauth
def listService():
    global client
    status = client.vault.service.list(client.authtok, None)
    return status

@try_connect
@reauth
def editService(servid, informations):
    global client
    if not informations["parent_service_id"]:
        informations["parent_service_id"] = 0
    status = client.vault.service.put(client.authtok, servid, informations)
    return status

@try_connect
@reauth
def delService(servid):
    global client
    status = client.vault.service_del(client.authtok, servid)
    return status

@try_connect
@reauth
def addUserGroup(group_id, user, is_admin):
    global client
    # TODO: USE this following function
    # status = client.vault.group_add_user(client.authtok, group_id, user, is_admin, symkey)
    # Cause symkey => HOWTO to get this !
    # Not is one ...
    status = client.group_add_user(group_id, user, is_admin)
    # For now ...
    return status

@try_connect
@reauth
def delUserGroup(group_id, user):
    global client
    status = client.vault.group_del_user(client.authtok, group_id, user)
    return status

@try_connect
@reauth
def addGroup(group_name):
    global client
    status = client.vault.group_add(client.authtok, group_name)
    return status
  
@try_connect
@reauth
def delGroup(group_id):
    global client
    status = client.vault.group_del(client.authtok, group_id)
    return status

@try_connect
@reauth
def addServiceGroup(group_id, service_id):
    global client
    # TODO: USE this following function
    # status = client.vault.group_add_service(client.authtok, group_id, service_id, symkey)
    # Cause symkey => HOWTO to get this !
    # Not is one ...
    status = client.group_add_service(group_id, service_id)
    # For now ...
    return status

@return_user
@try_connect
def delServiceGroup(group_id, service_id):
    global client
    status = client.vault.group_del_service(client.authtok, group_id, service_id)
    return status
