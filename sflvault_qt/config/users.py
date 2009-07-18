#!/usr/bin/env python
# -*- coding: UTF-8 -*-
#
#    sflvault_qt/config/users.py
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

import sys
from PyQt4 import QtCore, QtGui
import re
from PyQt4.QtCore import Qt
import sflvault
from sflvault.client import SFLvaultClient
import shutil
import os

from lib.auth import *


class UsersWidget(QtGui.QDialog):
    def __init__(self, parent=None):
        QtGui.QDialog.__init__(self, parent)
        self.parent = parent
        self.settings = self.parent.settings

        # Load gui items
        groupbox = QtGui.QGroupBox(self.tr("Groups"))
        self.usernameLabel = QtGui.QLabel(self.tr("User name"))
        self.username = QtGui.QLineEdit()
        self.idLabel = QtGui.QLabel(self.tr("Id"))
        self.id = QtGui.QLineEdit()
        self.adminLabel = QtGui.QLabel(self.tr("Admin"))
        self.admin = QtGui.QCheckBox()
        self.setup_expiredLabel = QtGui.QLabel(self.tr("Setup Expired"))
        self.setup_expired = QtGui.QCheckBox()
        self.waiting_setupLabel = QtGui.QLabel(self.tr("Waiting Setup"))
        self.waiting_setup = QtGui.QCheckBox()
        self.created_stampLabel = QtGui.QLabel(self.tr("Created at : "))
        self.created_stamp = QtGui.QDateTimeEdit()
        self.group_list = QtGui.QTreeView(self)
        self.group_list.setSelectionBehavior(QtGui.QAbstractItemView.SelectRows)
        self.group_list.setSelectionMode(QtGui.QAbstractItemView.ExtendedSelection)
        self.group_list.setEditTriggers(QtGui.QAbstractItemView.NoEditTriggers)
        self.group_list.setRootIsDecorated(False)
        self.group_list_filter = QtGui.QLineEdit(self)

        userbox = QtGui.QGroupBox(self.tr("Users"))
        self.user_add = QtGui.QPushButton(self.tr("New user"))
        self.user_delete = QtGui.QPushButton(self.tr("Delete user"))
        self.user_list = QtGui.QTreeView(self)
        self.user_list.setSelectionBehavior(QtGui.QAbstractItemView.SelectRows)
        self.user_list.setEditTriggers(QtGui.QAbstractItemView.NoEditTriggers)
        self.user_list.setRootIsDecorated(False)
        self.user_list_filter = QtGui.QLineEdit(self)
        
        okButton = QtGui.QPushButton(self.tr("OK"))
        cancelButton = QtGui.QPushButton(self.tr("Cancel"))

        # Load model
        self.model_group = GroupsModel(self)
        self.group_proxy = GroupsProxy()
        self.group_proxy.setSourceModel(self.model_group) 
        self.group_list.setModel(self.group_proxy)

        self.user_proxy = UsersProxy()
        self.user_list.setModel(self.user_proxy)

        # Positionning items
        ## Groups groupbox
        gridLayout = QtGui.QGridLayout()
        gridLayout.addWidget(self.usernameLabel,0,0)
        gridLayout.addWidget(self.username,0,1)
        gridLayout.addWidget(self.idLabel,1,0)
        gridLayout.addWidget(self.id,1,1)
        gridLayout.addWidget(self.adminLabel,2,0)
        gridLayout.addWidget(self.admin,2,1)
        gridLayout.addWidget(self.setup_expiredLabel,3,0)
        gridLayout.addWidget(self.setup_expired,3,1)
        gridLayout.addWidget(self.waiting_setupLabel,4,0)
        gridLayout.addWidget(self.waiting_setup,4,1)
        gridLayout.addWidget(self.created_stampLabel,5,0)
        gridLayout.addWidget(self.created_stamp,5,1)
        gridLayout.addWidget(self.group_list_filter,6,0,1,3)
        gridLayout.addWidget(self.group_list,7,0,5,3)

        groupbox.setLayout(gridLayout)

        ## User groupbox
        gridLayout = QtGui.QGridLayout()
        gridLayout.addWidget(self.user_add, 0, 0)
        gridLayout.addWidget(self.user_delete, 0, 2)
        gridLayout.addWidget(self.user_list_filter,1,0,1,3)
        gridLayout.addWidget(self.user_list,2,0,5,3)
        userbox.setLayout(gridLayout)

        buttonLayout = QtGui.QHBoxLayout()
        buttonLayout.addStretch(1)
        buttonLayout.addWidget(okButton)
        buttonLayout.addWidget(cancelButton)

        mainLayout = QtGui.QGridLayout()
        mainLayout.addWidget(userbox,0,0)
        mainLayout.addWidget(groupbox,0,1)
        mainLayout.addLayout(buttonLayout,2,0,1,2)
        self.setLayout(mainLayout)

        self.setWindowTitle(self.tr("Users management"))

        # SIGNALS
        self.connect(self.user_list_filter, QtCore.SIGNAL("textChanged (const QString&)"), self.user_proxy.setFilterRegExp)
        self.connect(self.user_add, QtCore.SIGNAL("clicked()"), self.newUser)
        self.connect(self.user_delete, QtCore.SIGNAL("clicked()"), self.deleteUser)
        self.connect(self.user_list, QtCore.SIGNAL("clicked (const QModelIndex&)"), self.editUser)
        self.connect(self.group_list_filter, QtCore.SIGNAL("textChanged (const QString&)"), self.group_proxy.setFilterRegExp)
        self.connect(cancelButton, QtCore.SIGNAL("clicked()"), self, QtCore.SLOT("reject()"))

    def exec_(self):
        # Get users list
        self.loadUserList()
        # Get services list
        self.groups = listGroup()
        # Show dialog
        self.show()

    def deleteUser(self):
        """
            Delete selected user
        """
        if self.user_list.selectedIndexes():
            name = unicode(self.user_list.selectedIndexes()[0].data().toString())
            delUser(name)
            self.loadUserList()


    def editUser(self):
        """
        """
        if self.user_list.selectedIndexes():
            name = unicode(self.user_list.selectedIndexes()[0].data().toString())
            id = int(self.user_list.selectedIndexes()[1].data().toString().split("#")[1])
            # Find user in user list
            for user in self.model_user.users:
                if user["id"] == id:
                    self.username.setText(user["username"])
                    self.id.setText(QtCore.QString(user["id"]))
                    if user["is_admin"]:
                        self.admin.setCheckState(QtCore.Qt.Checked)
                    else:
                        self.admin.setCheckState(QtCore.Qt.Unchecked)
                    if user["setup_expired"]:
                        self.setup_expired.setCheckState(QtCore.Qt.Checked)
                    else:
                        self.setup_expired.setCheckState(QtCore.Qt.Unchecked)
                    if user["waiting_setup"]:
                        self.waiting_setup.setCheckState(QtCore.Qt.Checked)
                    else:
                        self.waiting_setup.setCheckState(QtCore.Qt.Unchecked)
                    from datetime import datetime
                    print dir(user["created_stamp"])
                    print user["created_stamp"].value
#                    print user["created_stamp"].strftime("%Y, %m, %d, %H, %M, %s")
                    datetime = QtCore.QDateTime()
                    datetime.fromString(QtCore.QString(user["created_stamp"].value), "yyyyMMddTHH:mm:ss")
                    print datetime.date()
                    self.created_stamp.setDateTime(datetime)
                    break

            print 'eee'

    def newUser(self):
        """
        """
        # Show input Dialog
        newUser = NewUserWidget(self)
        newUser.exec_()


    def loadUserList(self):
        """
            Load User model
        """
        users = listUsers()
        print users
        self.model_user = UsersModel(users, parent=self)
        self.user_proxy.setSourceModel(self.model_user)


    def fillTables(self):
        # Delete old model
        if self.model_user_group:
            del self.model_user_group 
        if self.model_user:
            del self.model_user
        # Test if an item is seleted
        if not len(self.group_list.selectedIndexes()):
            return False
        # Get selected ID
        groupindex = self.group_list.selectedIndexes()[1]
        groupid, bool = groupindex.data(QtCore.Qt.DisplayRole).toInt()
        # Create new model and associate with proxymodel
        self.model_user_group = UsersModel()
        self.user_group_proxy.setSourceModel(self.model_user_group)
        self.model_user = UsersModel()
        self.user_proxy.setSourceModel(self.model_user)
        # Send users in the good table
        for user in self.users:
            ids = []
            for group in user["groups"]:
                ids.append(group["id"])
            if groupid in ids:
                self.model_user_group.addUser(user["username"], user["id"])
            else:
                self.model_user.addUser(user["username"], user["id"])



class UsersProxy(QtGui.QSortFilterProxyModel):
    def __init__(self, parent=None):
        QtGui.QSortFilterProxyModel.__init__(self, parent)
        self.parent = parent
        self.setDynamicSortFilter(1)
        self.setSortCaseSensitivity(QtCore.Qt.CaseInsensitive)

    def filterAcceptsRow(self, sourceRow, sourceParent):
        """
            Permit to filter on 2 first columns
        """
        # By name
        index_name = self.sourceModel().index(sourceRow,0,sourceParent)
        # By id
        index_id = self.sourceModel().index(sourceRow,1,sourceParent)
        # Get pattern
        pattern = self.filterRegExp().pattern()
        # If pattern is in id or name, show it !
        if unicode(index_id.data(0).toString()).find(pattern) != -1 or \
            unicode(index_name.data(0).toString()).find(pattern) != -1:
            return True
        return False


class UsersModel(QtGui.QStandardItemModel):
    def __init__(self, users, parent=None):
        QtGui.QStandardItemModel.__init__(self, 0, 2, parent)
        self.parent = parent
        self.setHeaders()
        self.users = users
        for user in users:
            self.addUser(user["username"], "u#" + unicode(user["id"]))

    def setHeaders(self):
        self.setColumnCount(2)
        self.setRowCount(0)
        self.setHeaderData(0, QtCore.Qt.Horizontal, QtCore.QVariant("Name"))
        self.setHeaderData(1, QtCore.Qt.Horizontal, QtCore.QVariant("Id"))

    def addUser(self, name=None, id=None):
        self.insertRow(0)
        self.setData(self.index(0, 0), QtCore.QVariant(name))
        self.setData(self.index(0, 1), QtCore.QVariant(id))

    def delUser(self):
        """
            Delete selected row
        """
        # Delete current row
        selected_row = self.parent.group_list.selectedIndexes()[0]
        self.removeRows(selected_row.row(), 1)
        

class GroupsProxy(QtGui.QSortFilterProxyModel):
    def __init__(self, parent=None):
        QtGui.QSortFilterProxyModel.__init__(self, parent)
        self.parent = parent
        self.setDynamicSortFilter(1)
        self.setSortCaseSensitivity(QtCore.Qt.CaseInsensitive)

    def filterAcceptsRow(self, sourceRow, sourceParent):
        """
            Permit to filter on 2 last columns
        """
        # By name
        index_name = self.sourceModel().index(sourceRow,1,sourceParent)
        # By id
        index_id = self.sourceModel().index(sourceRow,2,sourceParent)
        # Get pattern
        pattern = self.filterRegExp().pattern()
        # If pattern is in id or name, show it !
        if unicode(index_id.data(0).toString()).find(pattern) != -1 or \
            unicode(index_name.data(0).toString()).find(pattern) != -1:
            return True
        return False


class GroupsModel(QtGui.QStandardItemModel):
    def __init__(self, parent=None):
        QtGui.QStandardItemModel.__init__(self, 0, 2, parent)
        self.parent = parent
        self.setHeaders()
        self.groups = []
        self.columns = ['checked', 'name', 'id']

    def setHeaders(self):
        self.setColumnCount(3)
        self.setRowCount(0)
        self.setHeaderData(0, QtCore.Qt.Horizontal, QtCore.QVariant("Check"))
        self.setHeaderData(1, QtCore.Qt.Horizontal, QtCore.QVariant("Name"))
        self.setHeaderData(2, QtCore.Qt.Horizontal, QtCore.QVariant("Id"))

    def loadGroupList(self):
        """
            Get all groups
        """
        for group in self.parent.groups:
            self.addGroup(group["name"], group["id"])
        
    def addGroup(self, checked=QtCore.Qt.Unchecked, name=None, id=None,):
        self.insertRow(0)
        self.groups.append(GroupItem(checked, name, id))

    def flags(self, index):
        f = QtCore.QAbstractTableModel.flags(self,index)
        if index.column() == 0:
            f |= QtCore.Qt.ItemIsUserCheckable
        return f

    def data(self, index, role):
        # if index is not valid
        if not index.isValid():
            return QtCore.QVariant()
        # if protocols is empty
        if not self.groups:
            return QtCore.QVariant()

        group = self.groups[index.row()]

        # get value of the checkbox
        if role == QtCore.Qt.CheckStateRole:
            if index.column() == 0:
                attrName = self.columns[index.column()]
                value = getattr(group, attrName)
                return QtCore.QVariant(value)

        # get value of protocol name and command
        if role in [QtCore.Qt.EditRole, QtCore.Qt.DisplayRole]:
            if index.column() == 1 or index.column() == 2:
                attrName = self.columns[index.column()]
                value = getattr(group, attrName)
                if attrName == "id":
                    value = "g#" + unicode(value)
                return QtCore.QVariant(value)

        return QtCore.QVariant()

    def setData(self, index, value, role):
        # if index is not valid
        if not index.isValid():
            return False
        # if groups is empty
        if not self.groups:
            return False

        # Get group item
        group = self.groups[index.row()]

        # Set attributes
        attrName = self.columns[index.column()]
        result = group.setData(value, attrName)

        if result:
            self.dataChanged.emit(index, index)

        return result



class GroupItem(QtCore.QObject):
    def __init__(self, checked, name, id):
        self.name = name
        self.id = id
        self.checked = checked

    def setData(self, value, attr):
        """
            Set attributes
        """
        if attr == "checked":
            value, bool = value.toInt()
            if bool:
                self.checked = value
                return True

        return False

class NewUserWidget(QtGui.QDialog):
    def __init__(self, parent=None):
        QtGui.QDialog.__init__(self, parent)
        self.parent = parent

        # Load gui items
        groupbox = QtGui.QGroupBox()
        self.nameLabel = QtGui.QLabel(self.tr("User Name : "))
        self.name = QtGui.QLineEdit()
        self.adminLabel = QtGui.QLabel(self.tr("Admin : "))
        self.admin = QtGui.QCheckBox()

        self.save = QtGui.QPushButton(self.tr("Save user"))
        self.cancel = QtGui.QPushButton(self.tr("Cancel"))

        # Positionning items
        ## Groups groupbox
        gridLayout = QtGui.QGridLayout()
        gridLayout.addWidget(self.nameLabel,0,0)
        gridLayout.addWidget(self.name,0,1)
        gridLayout.addWidget(self.adminLabel,1,0)
        gridLayout.addWidget(self.admin,1,1)
        gridLayout.addWidget(self.save,2,0)
        gridLayout.addWidget(self.cancel,2,1)
        groupbox.setLayout(gridLayout)

        mainLayout = QtGui.QGridLayout()
        mainLayout.addWidget(groupbox,0,0)
        self.setLayout(mainLayout)

        self.setWindowTitle(self.tr("New user"))

        # SIGNALS
        self.connect(self.save, QtCore.SIGNAL("clicked()"), self, QtCore.SLOT("accept()"))
        self.connect(self.cancel, QtCore.SIGNAL("clicked()"), self, QtCore.SLOT("reject()"))

    def accept(self):
        username = unicode(self.name.text())
        if self.admin.checkState() == QtCore.Qt.Checked:
            admin = True
        else:
            admin = False
        # Add user
        status = addUser(username, admin)
        # Reload user list if no error
        if not status["error"]:
            self.parent.loadUserList()
            self.done(status["user_id"])
        else:
            self.done(0)
