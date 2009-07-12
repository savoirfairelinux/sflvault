#!/usr/bin/env python
# -*- coding: UTF-8 -*-

import sys
from PyQt4 import QtCore, QtGui
import re
from PyQt4.QtCore import Qt
import sflvault
from sflvault.client import SFLvaultClient
import shutil
import os

from lib.auth import *
#token = getAuth()


class GroupsWidget(QtGui.QDialog):
    def __init__(self, parent=None):
        QtGui.QDialog.__init__(self, parent)
        self.parent = parent
        self.settings = self.parent.settings
        self.protocols = {}

        # Load gui items
        groupbox = QtGui.QGroupBox(self.tr("Groups"))
        self.group_add = QtGui.QPushButton(self.tr("New group"))
        self.group_edit = QtGui.QPushButton(self.tr("Edit group"))
        self.group_delete = QtGui.QPushButton(self.tr("Delete group"))
        self.group_list = QtGui.QTreeView(self)
        self.group_list.setSelectionBehavior(QtGui.QAbstractItemView.SelectRows)
        self.group_list.setSelectionMode(QtGui.QAbstractItemView.ExtendedSelection)
        self.group_list.setEditTriggers(QtGui.QAbstractItemView.NoEditTriggers)
        self.group_list.setRootIsDecorated(False)
        self.group_list_filter = QtGui.QLineEdit(self)

        servicebox = QtGui.QGroupBox(self.tr("Services"))
        self.service_add = QtGui.QPushButton(self.tr("Add services"))
        self.service_remove = QtGui.QPushButton(self.tr("Remove services"))
        self.service_list = QtGui.QTableView(self)
        self.service_list_filter = QtGui.QLineEdit(self)
        self.service_group_list = QtGui.QTableView(self)
        self.service_group_list_filter = QtGui.QLineEdit(self)

        userbox = QtGui.QGroupBox(self.tr("Users"))
        self.user_add = QtGui.QPushButton(self.tr("Add users"))
        self.user_remove = QtGui.QPushButton(self.tr("Remove users"))
        self.user_list = QtGui.QTreeView(self)
        self.user_list.setSelectionBehavior(QtGui.QAbstractItemView.SelectRows)
        self.user_list.setSelectionMode(QtGui.QAbstractItemView.ExtendedSelection)
        self.user_list.setEditTriggers(QtGui.QAbstractItemView.NoEditTriggers)
        self.user_list.setRootIsDecorated(False)
        self.user_list_filter = QtGui.QLineEdit(self)
        self.user_group_list = QtGui.QTreeView(self)
        self.user_group_list.setSelectionBehavior(QtGui.QAbstractItemView.SelectRows)
        self.user_group_list.setSelectionMode(QtGui.QAbstractItemView.ExtendedSelection)
        self.user_group_list.setEditTriggers(QtGui.QAbstractItemView.NoEditTriggers)
        self.user_group_list.setRootIsDecorated(False)
        self.user_group_list_filter = QtGui.QLineEdit(self)
        
        okButton = QtGui.QPushButton(self.tr("OK"))
        cancelButton = QtGui.QPushButton(self.tr("Cancel"))

        # Load model
        self.model_group = GroupsModel(self)
        self.group_proxy = GroupsProxy()
        self.group_proxy.setSourceModel(self.model_group) 
        self.group_list.setModel(self.group_proxy)

        self.model_user = UsersModel(self)
        self.user_proxy = UsersProxy()
        self.user_proxy.setSourceModel(self.model_user) 
        self.user_list.setModel(self.user_proxy)
        self.model_user_group = UsersModel(self)
        self.user_group_proxy = UsersProxy()
        self.user_group_proxy.setSourceModel(self.model_user_group) 
        self.user_group_list.setModel(self.user_group_proxy)
#        self.protocol_list = QtGui.QTableView(self)
#        self.protocol_list.setModel(self.model)
#        self.protocol_list.setSelectionBehavior(QtGui.QAbstractItemView.SelectRows)
#        self.protocol_list.setSortingEnabled(1)
#        self.protocol_list.setSelectionMode(QtGui.QAbstractItemView.SingleSelection)
#        self.protocol_list.adjustSize()
        ### MARCHE PAS
#        h = self.protocol_list.horizontalHeader()
#        h.setResizeMode(0, QtGui.QHeaderView.Fixed)
#        h.setResizeMode(1, QtGui.QHeaderView.Interactive)
#        h.setResizeMode(2, QtGui.QHeaderView.Stretch)
#        h.resizeSection(0,50)
#        h.resizeSection(1,2000)

        # Positionning items
        ## Groups groupbox
        gridLayout = QtGui.QGridLayout()
        gridLayout.addWidget(self.group_add,2,1)
        gridLayout.addWidget(self.group_edit,3,1)
        gridLayout.addWidget(self.group_delete,4,1)
        gridLayout.addWidget(self.group_list_filter,0,3)
        gridLayout.addWidget(self.group_list,1,3,5,1)
        groupbox.setLayout(gridLayout)

        ## Service groupbox
        gridLayout = QtGui.QGridLayout()
        gridLayout.addWidget(self.service_add,2,2)
        gridLayout.addWidget(self.service_remove,4,2)
        gridLayout.addWidget(self.service_list_filter,0,0,1,2)
        gridLayout.addWidget(self.service_list,1,0,5,2)
        gridLayout.addWidget(self.service_group_list_filter,0,3,1,2)
        gridLayout.addWidget(self.service_group_list,1,3,5,2)
        servicebox.setLayout(gridLayout)

        ## User groupbox
        gridLayout = QtGui.QGridLayout()
        gridLayout.addWidget(self.user_add,2,2)
        gridLayout.addWidget(self.user_remove ,4,2)
        gridLayout.addWidget(self.user_list_filter,0,0,1,2)
        gridLayout.addWidget(self.user_list,1,0,5,2)
        gridLayout.addWidget(self.user_group_list_filter,0,3,1,2)
        gridLayout.addWidget(self.user_group_list,1,3,5,2)
        userbox.setLayout(gridLayout)

        buttonLayout = QtGui.QHBoxLayout()
        buttonLayout.addStretch(1)
        buttonLayout.addWidget(okButton)
        buttonLayout.addWidget(cancelButton)

        mainLayout = QtGui.QGridLayout()
        mainLayout.addWidget(groupbox,0,0,1,2)
        mainLayout.addWidget(servicebox,1,0)
        mainLayout.addWidget(userbox,1,1)
        mainLayout.addLayout(buttonLayout,2,0,1,2)
        self.setLayout(mainLayout)

        self.setWindowTitle(self.tr("Groups management"))

        # SIGNALS
        self.connect(self.user_list_filter, QtCore.SIGNAL("textChanged (const QString&)"), self.user_proxy.setFilterRegExp)
        self.connect(self.user_group_list_filter, QtCore.SIGNAL("textChanged (const QString&)"), self.user_group_proxy.setFilterRegExp)
        self.connect(self.group_list, QtCore.SIGNAL("clicked (const QModelIndex&)"), self.fillTables)
        self.connect(self.group_list_filter, QtCore.SIGNAL("textChanged (const QString&)"), self.group_proxy.setFilterRegExp)
#        self.connect(self.addprotocol, QtCore.SIGNAL("clicked()"), self.model.addProtocol)
#        self.connect(self.removeprotocol, QtCore.SIGNAL("clicked()"), self.model.delProtocol)
#        self.connect(okButton, QtCore.SIGNAL("clicked()"), self.saveConfig)
        self.connect(cancelButton, QtCore.SIGNAL("clicked()"), self, QtCore.SLOT("reject()"))

    def exec_(self):
        # Get users list
        self.users = getUserList()
        # Get services list
        # TODO
#        self.services = token.vault.user_list(token.authtok, True)["list"]
        # Show dialog
        self.show()

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

    def connection(self):
        self.model_group.getAllGroups()


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
    def __init__(self, parent=None):
        QtGui.QStandardItemModel.__init__(self, 0, 2, parent)
        self.parent = parent
        self.setHeaders()

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


class ServicesProxy(QtGui.QSortFilterProxyModel):
    def __init__(self, parent=None):
        QtGui.QSortFilterProxyModel.__init__(self, parent)
        self.parent = parent
        self.setDynamicSortFilter(1)
        self.setSortCaseSensitivity(QtCore.Qt.CaseInsensitive)


class ServicesModel(QtGui.QStandardItemModel):
    def __init__(self, parent=None):
        QtGui.QStandardItemModel.__init__(self, 0, 2, parent)
        self.parent = parent
        self.setHeaders()

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


class GroupsModel(QtGui.QStandardItemModel):
    def __init__(self, parent=None):
        QtGui.QStandardItemModel.__init__(self, 0, 2, parent)
        self.parent = parent
        self.setHeaders()

    def setHeaders(self):
        self.setColumnCount(2)
        self.setRowCount(0)
        self.setHeaderData(0, QtCore.Qt.Horizontal, QtCore.QVariant("Name"))
        self.setHeaderData(1, QtCore.Qt.Horizontal, QtCore.QVariant("Id"))

    def getAllGroups(self):
        """
            Get all groups
        """
        groups = listGroup()["list"]
        for group in groups:
            self.addGroup(group["name"], group["id"])
        
    def addGroup(self, name=None, id=None):
        self.insertRow(0)
        self.setData(self.index(0, 0), QtCore.QVariant(name))
        self.setData(self.index(0, 1), QtCore.QVariant(id))

    def delGroup(self):
        """
            Delete selected row
        """
        # Delete current row
        selected_row = self.parent.group_list.selectedIndexes()[0]
        self.removeRows(selected_row.row(), 1)


