#!/usr/bin/env python
# -*- coding: utf-8 -*-
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

from sflvault.clientqt.lib.auth import *
from sflvault.clientqt.gui.dialog import progressdialog


class UsersWidget(QtGui.QDialog):
    def __init__(self, parent=None):
        QtGui.QDialog.__init__(self, parent)
        self.parent = parent
        self.settings = self.parent.settings

        # Load gui items
        userinfobox = QtGui.QGroupBox(self.tr("User Information"))
        self.usernameLabel = QtGui.QLabel(self.tr("User name"))
        self.username = QtGui.QLineEdit()
        self.username.setReadOnly(True)
        self.idLabel = QtGui.QLabel(self.tr("Id"))
        self.id = QtGui.QLineEdit()
        self.id.setReadOnly(True)
        self.adminLabel = QtGui.QLabel(self.tr("Admin"))
        self.admin = QtGui.QCheckBox()
        self.admin.setEnabled(False)
        self.setup_expiredLabel = QtGui.QLabel(self.tr("Setup Expired"))
        self.setup_expired = QtGui.QCheckBox()
        self.setup_expired.setEnabled(False)
        self.waiting_setupLabel = QtGui.QLabel(self.tr("Waiting Setup"))
        self.waiting_setup = QtGui.QCheckBox()
        self.waiting_setup.setEnabled(False)
        self.created_stampLabel = QtGui.QLabel(self.tr("Created at : "))
        self.created_stamp = QtGui.QDateTimeEdit()
        self.created_stamp.setReadOnly(True)
        groupbox = QtGui.QGroupBox(self.tr("Groups"))
        self.group_add = QtGui.QPushButton(self.tr("New group"))
        self.group_delete = QtGui.QPushButton(self.tr("Delete group"))
        self.group_list = QtGui.QTableView(self)
        self.group_list.setSelectionBehavior(QtGui.QAbstractItemView.SelectRows)
        self.group_list.setSortingEnabled(1)
        self.group_list.setSelectionMode(QtGui.QAbstractItemView.SingleSelection)
        self.group_list_filter_label = QtGui.QLabel(self.tr("Filter"))
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
        ## User information groupbox
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
        userinfobox.setLayout(gridLayout)
        
        ## Groups groupbox
        gridLayout = QtGui.QGridLayout()
        gridLayout.addWidget(self.group_add,0,0)
        gridLayout.addWidget(self.group_delete,0,2)
        gridLayout.addWidget(self.group_list_filter_label,7,0)
        gridLayout.addWidget(self.group_list_filter,7,1,1,2)
        gridLayout.addWidget(self.group_list,1,0,5,3)
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
        mainLayout.addWidget(userbox,0,0,2,1)
        mainLayout.addWidget(userinfobox,0,1)
        mainLayout.addWidget(groupbox,1,1)
        mainLayout.addLayout(buttonLayout,2,0,1,2)
        self.setLayout(mainLayout)

        self.setWindowTitle(self.tr("Users management"))

        # SIGNALS
        self.connect(self.user_list_filter, QtCore.SIGNAL("textChanged (const QString&)"), self.user_proxy.setFilterRegExp)
        self.connect(self.user_add, QtCore.SIGNAL("clicked()"), self.newUser)
        self.connect(self.group_add, QtCore.SIGNAL("clicked()"), self.newGroup)
        self.connect(self.user_delete, QtCore.SIGNAL("clicked()"), self.deleteUser)
        self.connect(self.group_delete, QtCore.SIGNAL("clicked()"), self.deleteGroup)
        self.connect(self.user_list, QtCore.SIGNAL("activated (const QModelIndex&)"), self.editUser)
        self.connect(self.group_list_filter, QtCore.SIGNAL("textChanged (const QString&)"), self.group_proxy.setFilterRegExp)
        self.connect(cancelButton, QtCore.SIGNAL("clicked()"), self, QtCore.SLOT("reject()"))

    def exec_(self):
        if not self.parent.userinfo["is_admin"]:
            self.user_add.setDisabled(1)
            self.user_delete.setDisabled(1)
        # Get users list
        self.loadUserList()
        # Show dialog
        self.show()

    def deleteGroup(self):
        """
            Delete selected group
        """
        if self.group_list.selectedIndexes():
            name = unicode(self.group_list.selectedIndexes()[0].data().toString())
            selected_group = self.model_group.groups[self.group_list.selectedIndexes()[0].row()]

            pdialog = progressdialog.ProgressDialog("Deleting a group",
                "Please wait while deleting a group",
                delGroup, selected_group.id)
            ret = pdialog.run()

            if ret:
                message = QtGui.QMessageBox(QtGui.QMessageBox.Information, self.tr("Delete group"), self.tr("Group %s deleted successfully" % unicode(selected_group.id)))
                message.exec_()
                self.editUser() 
                return True
            else:
                return False


    def deleteUser(self):
        """
            Delete selected user
        """
        if self.user_list.selectedIndexes():
            name = unicode(self.user_list.selectedIndexes()[0].data().toString())
            delUser(name)
            self.loadUserList()

    def updateInfo(self):
        # Get your informations
        self.parent.userinfo = getUserInfo(str(self.settings.value("SFLvault/username").toString()))
        # Get groups list
        self.groups = listGroup()
        # Update users info
        users = listUsers(True)
        self.model_user = UsersModel(users, parent=self)

    def editUser(self):
        """
        """
        if self.user_list.selectedIndexes():
            self.updateInfo()
            self.model_group.groups = []
            self.model_group.setHeaders() 
            self.current_username = unicode(self.user_list.selectedIndexes()[0].data().toString())
            id = int(self.user_list.selectedIndexes()[1].data().toString().split("#")[1])
            # Find user in user list
            for user in self.model_user.users:
                if user["id"] == id:
                    # Fill user form
                    self.username.setText(user["username"])
                    self.id.setText(unicode(user["id"]))
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
                        self.group_list.setDisabled(1)
                    else:
                        self.waiting_setup.setCheckState(QtCore.Qt.Unchecked)
                        self.group_list.setDisabled(0)
                    datetime = QtCore.QDateTime.fromString(user["created_stamp"].value, "yyyyMMddTHH:mm:ss")
                    self.created_stamp.setDateTime(datetime)
                    self.created_stamp.setDisplayFormat("yyyy-MM-dd HH:mm:ss")
                    # Load all groups
                    for group in self.groups["list"]:
                        # Do not show group which you are not member
                        if not group["name"] in [yourgroup["name"]  for yourgroup in self.parent.userinfo["groups"] ]:
                            continue
                        group_member = False
                        # browser user groups
                        for user_group in user["groups"]:
                            #print user_group
                            # check if user is in group
                            if user_group["id"] == group["id"]:
                                group_member = True
                                # Check if is group admin
                                if user_group["is_admin"]:
                                    # Add it as admin
                                    self.model_group.addGroup(QtCore.Qt.Checked, QtCore.Qt.Checked, group["name"], group["id"])
                                else:
                                    # Add it as member
                                    self.model_group.addGroup(QtCore.Qt.Unchecked, QtCore.Qt.Checked, group["name"], group["id"])
                        if not group_member:
                            # Add group
                            self.model_group.addGroup(QtCore.Qt.Unchecked, QtCore.Qt.Unchecked, group["name"], group["id"])
                    break

    def newGroup(self):
        """ Create a new group
        """
        # Show input Dialog
        group_name, ok = QtGui.QInputDialog.getText(self.parent, self.tr("New group"),
                                                self.tr("New group name :"),
                                                QtGui.QLineEdit.Normal)
        if not ok or not group_name:
            return False

        pdialog = progressdialog.ProgressDialog("Creating a new group",
            "Please wait while creating a new group",
            addGroup, unicode(group_name))
        ret = pdialog.run()

        if ret:
            message = QtGui.QMessageBox(QtGui.QMessageBox.Information, self.tr("Create group"), self.tr("Group %s created successfully" % unicode(group_name)))
            message.exec_()
            self.editUser()
            return True
        else:
            return False


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
        users = listUsers(True)
        self.model_user = UsersModel(users, parent=self)
        self.user_proxy.setSourceModel(self.model_user)


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
        if users != False:
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
        index_name = self.sourceModel().index(sourceRow,2,sourceParent)
        # By id
        index_id = self.sourceModel().index(sourceRow,3,sourceParent)
        # Get pattern
        pattern = self.filterRegExp().pattern()
        # If pattern is in id or name, show it !
        if unicode(index_id.data(0).toString()).find(pattern) != -1 or \
            unicode(index_name.data(0).toString()).find(pattern) != -1:
            return True
        return False


class GroupsModel(QtGui.QStandardItemModel):
    def __init__(self, parent=None):
        QtGui.QStandardItemModel.__init__(self, parent)
        self.parent = parent
        self.setHeaders()
        self.groups = []
        self.columns = ['admin', 'member', 'name', 'id']

    def setHeaders(self):
        self.setColumnCount(4)
        self.setRowCount(0)
        self.setHeaderData(0, QtCore.Qt.Horizontal, QtCore.QVariant("Admin"))
        self.setHeaderData(1, QtCore.Qt.Horizontal, QtCore.QVariant("Member"))
        self.setHeaderData(2, QtCore.Qt.Horizontal, QtCore.QVariant("Name"))
        self.setHeaderData(3, QtCore.Qt.Horizontal, QtCore.QVariant("Id"))

    def addGroup(self, admin=QtCore.Qt.Unchecked, checked=QtCore.Qt.Unchecked, name=None, id=None,):
        self.insertRow(0)
        self.groups.append(GroupItem(admin, checked, name, id, self.parent))

    def flags(self, index):
        f = QtCore.QAbstractTableModel.flags(self,index)
        if index.column() == 0 or index.column() == 1:
            f |= QtCore.Qt.ItemIsUserCheckable
        return f

    def data(self, index, role):
        # if index is not valid
        if not index.isValid():
            return QtCore.QVariant()
        # if protocols is empty
        if not self.groups:
            return QtCore.QVariant()

        if len(self.groups) <= index.row():
            return QtCore.QVariant()

        group = self.groups[index.row()]

        # get value of member and admin
        if role == QtCore.Qt.CheckStateRole:
            if index.column() == 0 or index.column() == 1:
                attrName = self.columns[index.column()]
                value = getattr(group, attrName)
                return QtCore.QVariant(value)

        # get value of group name and id
        if role == QtCore.Qt.DisplayRole:
            if index.column() == 2 or index.column() == 3:
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
    def __init__(self, admin, member, name, id, parent=None):
        self.name = name
        self.parent = parent
        self.id = id
        self.admin = admin
        self.member = member

    def setData(self, value, attr):
        """
            Set attributes
        """
        if attr == "admin":
            value, bool = value.toInt()
            if bool:
                if value == QtCore.Qt.Checked:
                    # If user checks admin
                    if self.member == QtCore.Qt.Checked:
                        # if user is already in this group
                        ret = delUserGroup(self.id, self.parent.current_username)
                        if not ret:
                            # If can not delete user, do nothing
                            return False
                        pdialog = progressdialog.ProgressDialog("Adding user in group",
                                "Please wait while adding user as group admin",
                                addUserGroup, self.id, self.parent.current_username, True)
                        ret = pdialog.run()
                        
                    else:
                        # if user is not already in this group
                        pdialog = progressdialog.ProgressDialog("Adding user in group",
                                "Please wait while adding user as group admin",
                                addUserGroup, self.id, self.parent.current_username, True)
                        ret = pdialog.run()
                        # TODO ret cannot be FALSE cause lib.auth.addUsergroup can not return False ...
                        if not ret:
                            # If can not delete user, do nothing
                            return False
                        setattr(self, "member", QtCore.Qt.Checked)
                        
                else:
                    # If user unchecks admin
                    ret = delUserGroup(self.id, self.parent.current_username)
                    if not ret:
                        # If can not delete user, do nothing
                        return False
                    pdialog = progressdialog.ProgressDialog("Delete admin in group",
                            "Please wait while deleting this user as group admin ",
                            addUserGroup, self.id, self.parent.current_username, False)
                    ret = pdialog.run()

                if not ret:
                    # If can not delete user, do nothing
                    return False
                else:
                    setattr(self, attr, value)
                    return True

        if attr == "member":
            value, bool = value.toInt()
            if bool:
                if self.admin == QtCore.Qt.Checked:
                    is_admin = True
                else:
                    is_admin = False
                if value == QtCore.Qt.Checked:
                    # add user in group
                    pdialog = progressdialog.ProgressDialog("Adding user in group",
                                "Please wait while adding user in this group",
                                addUserGroup, self.id, self.parent.current_username, is_admin)
                    ret = pdialog.run()
                elif value == QtCore.Qt.Unchecked:
                    # del user in group
                    ret = delUserGroup(self.id, self.parent.current_username)
                    if not ret:
                        # If can not delete user, do nothing
                        return False
                    setattr(self, "admin", QtCore.Qt.Unchecked)
                else:
                    # Error ???
                    return False

                # Save action
                if ret == False:
                    setattr(self, attr, value)
                    return False
                else:
                    setattr(self, attr, value)
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
        if status != False:
            self.parent.loadUserList()
            self.done(status["user_id"])
        else:
            self.done(0)
