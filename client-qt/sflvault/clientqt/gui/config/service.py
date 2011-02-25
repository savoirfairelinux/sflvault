#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
#    sflvault_qt/config/service.py
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
import re
import shutil
import os
from functools import partial

from PyQt4 import QtCore, QtGui
from PyQt4.QtCore import Qt

import sflvault
from sflvault.client import SFLvaultClient
from sflvault.clientqt.gui.dialog import progressdialog
from sflvault.clientqt.lib.auth import *


class DeleteServiceWidget(QtGui.QMessageBox):
    def __init__(self, servid=None, parent=None):
        QtGui.QMessageBox.__init__(self, parent)
        self.parent = parent
        # Check if a line is selected
        if not servid:
            return False
        self.servid = servid
        # Test if service exist
        service = getService(servid)
        if not "services" in service:
            return False
        # Set windows
        self.setIcon(QtGui.QMessageBox.Question)
        self.ok = self.addButton(QtGui.QMessageBox.Ok)
        self.cancel = self.addButton(QtGui.QMessageBox.Cancel)
        self.setText(self.tr("Do you want to delete %s" % service["services"][-1]["url"]))

        # SIGNALS
        self.connect(self.ok, QtCore.SIGNAL("clicked()"), self, QtCore.SLOT("accept()"))
        self.connect(self.cancel, QtCore.SIGNAL("clicked()"), self, QtCore.SLOT("reject()"))

    def accept(self):
        # Delete service
        status = delService(self.servid)
        if status:
            # reload tree
            self.parent.search(None)
            self.done(1)


class EditServiceWidget(QtGui.QDialog):
    def __init__(self, servid=False, machid=None, parent=None):
        QtGui.QDialog.__init__(self, parent)
        self.parent = parent
        self.settings = self.parent.settings
        self.servid = servid
        self.machid = machid
        self.metadata = {}
        if not self.servid:
            self.mode = "add"
        else:
            self.mode = "edit"

        self.setMinimumWidth(500)

        # Load gui items
        ## Main groupbox
        groupbox = QtGui.QGroupBox()
        groupbox.setTitle(self.tr("Service"))

        # Service info groupbox
        info_layout = QtGui.QGridLayout()
        groupbox_info = QtGui.QGroupBox()
        groupbox_info.setTitle(self.tr("Service info"))
        groupbox_info.setLayout(info_layout)
        self.machineLabel = QtGui.QLabel(self.tr("Machine"))
        self.machineLabel.setMinimumWidth(100)
        self.machine = QtGui.QComboBox()
        self.machine.setEditable(1)
        self.parentservLabel = QtGui.QLabel(self.tr("Parent service"))
        self.parentservLabel.setMinimumWidth(100)
        self.parentserv = QtGui.QComboBox()
        self.parentserv.setEditable(1)
        self.groupsLabel = QtGui.QLabel(self.tr("Group"))
        self.groupsLabel.setMinimumWidth(100)
        self.groups = QtGui.QListWidget(self)
        self.groups.setSelectionMode(QtGui.QAbstractItemView.MultiSelection)
        self.notesLabel = QtGui.QLabel(self.tr("Notes"))
        self.notesLabel.setMinimumWidth(100)
        self.notes = QtGui.QLineEdit()
        info_layout.addWidget(self.machineLabel, 0, 0)
        info_layout.addWidget(self.machine, 0, 1)
        info_layout.addWidget(self.parentservLabel, 1, 0)
        info_layout.addWidget(self.parentserv, 1, 1)
        info_layout.addWidget(self.groupsLabel, 2, 0)
        info_layout.addWidget(self.groups, 2, 1)
        info_layout.addWidget(self.notesLabel, 3, 0)
        info_layout.addWidget(self.notes, 3, 1)

        # Metadata groupbox
        self.metadata_layout = QtGui.QGridLayout()
        self.groupbox_metadata = QtGui.QGroupBox()
        self.groupbox_metadata.setTitle(self.tr("Metadata"))
        self.groupbox_metadata.setLayout(self.metadata_layout)
        self.metadata_key_label = QtGui.QLabel(self.tr("Metadata key"))
        self.metadata_value_label = QtGui.QLabel(self.tr("Metadata value"))
        self.metadata_button = QtGui.QPushButton(self.tr("+"))
        self.metadata_button.adjustSize()
        w = self.metadata_button.height()
        self.metadata_button.setMaximumWidth(w)
        self.metadata_layout.addWidget(self.metadata_key_label, 0, 0)
        self.metadata_layout.addWidget(self.metadata_value_label, 0, 1)
        self.metadata_layout.addWidget(self.metadata_button, 1, 2)
        self.groupbox_metadata.setLayout(self.metadata_layout)
        info_layout.addWidget(self.groupbox_metadata, 4, 0, 1, 2)
        self.groupbox_metadata.hide()
        
        # Url groupbox
        url_layout = QtGui.QGridLayout()
        groupbox_url = QtGui.QGroupBox()
        groupbox_url.setTitle(self.tr("Url"))
        groupbox_url.setLayout(url_layout)
        self.usernameLabel = QtGui.QLabel(self.tr("Username"))
        self.usernameLabel.setMinimumWidth(100)
        self.username = QtGui.QLineEdit()
        self.hostLabel = QtGui.QLabel(self.tr("Host"))
        self.hostLabel.setMinimumWidth(100)
        self.host = QtGui.QLineEdit()
        self.portLabel = QtGui.QLabel(self.tr("Port"))
        self.portLabel.setMinimumWidth(100)
        self.port = QtGui.QLineEdit()
        self.schemeLabel = QtGui.QLabel(self.tr("Scheme"))
        self.scheme = QtGui.QLineEdit()
        self.paramsLabel = QtGui.QLabel(self.tr("Parameters"))
        self.paramsLabel.setMinimumWidth(100)
        self.params = QtGui.QLineEdit()
        self.urlLabel = QtGui.QLabel(self.tr("Url"))
        self.urlLabel.setMinimumWidth(100)
        self.urlLabel.hide()
        self.url = QtGui.QLineEdit()
        self.url.hide()
        url_layout.addWidget(self.schemeLabel, 0, 0)
        url_layout.addWidget(self.scheme, 0, 1)
        url_layout.addWidget(self.usernameLabel, 1, 0)
        url_layout.addWidget(self.username, 1, 1)
        url_layout.addWidget(self.hostLabel, 2, 0)
        url_layout.addWidget(self.host, 2, 1)
        url_layout.addWidget(self.portLabel, 3, 0)
        url_layout.addWidget(self.port, 3, 1)
        url_layout.addWidget(self.paramsLabel, 4, 0)
        url_layout.addWidget(self.params, 4, 1)
        url_layout.addWidget(self.urlLabel, 5, 0,)
        url_layout.addWidget(self.url, 5, 2)
        groupbox_url.setLayout(url_layout)

        # Password Groupbox
        password_layout = QtGui.QGridLayout()
        groupbox_password = QtGui.QGroupBox()
        groupbox_password.setTitle(self.tr("Secret"))
        groupbox_password.setLayout(password_layout)
        self.passwordLabel = QtGui.QLabel(self.tr("Password"))
        self.passwordLabel.setMaximumWidth(100)
        self.password = QtGui.QLineEdit()
        self.password_button = QtGui.QPushButton(self.tr("Show Password"))
        if self.mode == "edit":
            self.password.setReadOnly(1)
            self.password.setDisabled(1)
        else:
            self.password.setReadOnly(0)
        password_layout.addWidget(self.passwordLabel, 0, 0)
        password_layout.addWidget(self.password, 0, 1, 1, 2)
        password_layout.addWidget(self.password_button, 0, 3)

        # Button Groupbox
        button_layout = QtGui.QHBoxLayout()
        groupbox_button = QtGui.QGroupBox()
        groupbox_button.setLayout(button_layout)
        self.advanced = QtGui.QPushButton(self.tr("Advanced"))
        self.save = QtGui.QPushButton(self.tr("Save service"))
        self.cancel = QtGui.QPushButton(self.tr("Cancel"))
        button_layout.addWidget(self.advanced)
        button_layout.addWidget(self.save)
        button_layout.addWidget(self.cancel)

        # Positionning items
        # Main groupbox
        gridLayout = QtGui.QGridLayout()
        gridLayout.addWidget(groupbox_url, 1, 0, 1, 2)
        gridLayout.addWidget(groupbox_info, 2, 0, 1, 2)
        gridLayout.addWidget(groupbox_password, 6, 0, 1, 2)
        gridLayout.addWidget(groupbox_button, 7, 0, 1, 2)
        groupbox.setLayout(gridLayout)
        mainLayout = QtGui.QGridLayout()
        mainLayout.addWidget(groupbox,0,0)
        self.setLayout(mainLayout)

        self.setWindowTitle(self.tr("Add service"))

        self.machineline = self.machine.lineEdit()
        QtCore.QObject.connect(self.machineline, QtCore.SIGNAL("editingFinished()"), self.completeMachine)
        self.parentservline = self.parentserv.lineEdit()
        QtCore.QObject.connect(self.parentservline, QtCore.SIGNAL("editingFinished()"), self.completeParentserv)

        # SIGNALS
        self.connect(self.username, QtCore.SIGNAL("textEdited(const QString&)"), self.simple_to_advanced)
        self.connect(self.host, QtCore.SIGNAL("textEdited(const QString&)"), self.simple_to_advanced)
        self.connect(self.port, QtCore.SIGNAL("textEdited(const QString&)"), self.simple_to_advanced)
        self.connect(self.scheme, QtCore.SIGNAL("textEdited(const QString&)"), self.simple_to_advanced)
        self.connect(self.params, QtCore.SIGNAL("textEdited(const QString&)"), self.simple_to_advanced)
        self.connect(self.url, QtCore.SIGNAL("textEdited(const QString&)"), self.advanced_to_simple)
        self.connect(self.password_button, QtCore.SIGNAL("clicked()"), self.fill_password)

        self.connect(self.metadata_button, QtCore.SIGNAL("clicked()"), self.add_metadata)

        self.connect(self.advanced, QtCore.SIGNAL("clicked()"), self.switch_edit)
        self.connect(self.save, QtCore.SIGNAL("clicked()"), self.editService)
        self.connect(self.cancel, QtCore.SIGNAL("clicked()"), self, QtCore.SLOT("reject()"))

    def add_metadata(self):
        key, ret = QtGui.QInputDialog.getText(self,
                                            self.tr("New Metadata"),
                                            self.tr("Metadata key:"),
                                            QtGui.QLineEdit.Normal,
                                            '');
        if key == '':
            print "error"
        else:
            value, ret = QtGui.QInputDialog.getText(self,
                                            self.tr("New Metadata"),
                                            self.tr("Metadata value:"),
                                            QtGui.QLineEdit.Normal,
                                            '');
            if value == '':
                print "error"
            key_label = QtGui.QLabel(key)
            value_label = QtGui.QLabel(value)

            self.metadata[key_label] = value_label

            length = self.metadata_layout.count()
            self.metadata_layout.addWidget(key_label, length, 0)
            self.metadata_layout.addWidget(value_label, length, 1)
            self.metadata_layout.addWidget(self.metadata_button, length + 1, 2)
            del_button = QtGui.QPushButton("-")
            del_button.adjustSize()
            w = del_button.height()
            del_button.setMaximumWidth(w)
            del_button.key = key_label 
            temp_func = partial(self.del_metadata, del_button)
            self.connect(del_button, QtCore.SIGNAL("clicked()"), temp_func) 
            self.metadata_layout.addWidget(del_button, length, 2)


    def switch_edit(self):
        if self.advanced.text() == QtCore.QString(self.tr("Advanced")):
            # Hide simple fields
            self.usernameLabel.hide()
            self.username.hide()
            self.hostLabel.hide()
            self.host.hide()
            self.portLabel.hide()
            self.port.hide()
            self.schemeLabel.hide()
            self.scheme.hide()
            self.paramsLabel.hide()
            self.params.hide()
            # Show advanced url
            self.urlLabel.show()
            self.url.show()
            self.groupbox_metadata.show()
            self.metadata_button.show()
            self.advanced.setText(self.tr("Simple"))
        else:
            self.usernameLabel.show()
            self.username.show()
            self.hostLabel.show()
            self.host.show()
            self.portLabel.show()
            self.port.show()
            self.schemeLabel.show()
            self.scheme.show()
            self.paramsLabel.show()
            self.params.show()
            self.urlLabel.hide()
            self.url.hide()
            self.groupbox_metadata.hide()
            self.metadata_button.hide()
            self.advanced.setText(self.tr("Advanced"))

    def advanced_to_simple(self):
        advanced_url = unicode(self.url.text())
        # Split data
        if len(advanced_url.split("@")) > 2:
            temp = advanced_url.rsplit("@",1)
            username = temp[0].split("://")[-1]
            protocol = temp[0].split("://")[0]
            url = temp[1]
            url = QtCore.QUrl(protocol + "://" + url)
        else:
            url = QtCore.QUrl(advanced_url)
        username = unicode(url.userName())
        protocol = unicode(url.scheme())
        port = unicode(url.port() if url.port() > 0 else '')
        host = unicode(url.host())
        uri = unicode(url.path())
        # Set fields
        self.username.setText(username)
        self.host.setText(host)
        self.port.setText(port)
        self.scheme.setText(protocol)
        self.params.setText(uri)

    def simple_to_advanced(self):
        username = self.username.text()
        host = self.host.text()
        port = self.port.text()
        scheme = self.scheme.text()
        params = self.params.text()

        advanced_url = QtCore.QUrl()
        advanced_url.setScheme(scheme)
        advanced_url.setHost(host)
        advanced_url.setPort(port.toInt()[0] if port.toInt()[1] else -1)
        advanced_url.setPath(params)
        advanced_url.setUserName(username)
        self.url.setText(advanced_url.toString())

    def fill_password(self):
        decodedpassword = getPassword(self.servid)
        if decodedpassword != False:
            self.password.setText(decodedpassword)
            self.password.setEchoMode(QtGui.QLineEdit.Normal)
            self.password.setReadOnly(0)
            self.password.setDisabled(0)
        else:
            # TODO show error box (permission denied ?)
            pass

    def fillMachinesList(self):
        machines = listMachine()
        # Fill machine combo box
        selected_machine = self.machineline.text()
        for machine in machines["list"]:
            self.machine.addItem(machine['name'] + " - m#" + unicode(machine['id']), QtCore.QVariant(machine['id']))
        # Select good row
        index = self.machine.findText(" - " + selected_machine, QtCore.Qt.MatchEndsWith)
        if index > -1:
            self.machine.setCurrentIndex(index)

    def fillServicesList(self):
        parentserv = self.parentservline.text()
        services = listService()
        # Fill service combo box
        self.parentserv.addItem(self.tr("No parent"), QtCore.QVariant(None))
        for service in services["list"]:
            # Doesn t add this item in possible parent list (if it s edit mode
            if service['id'] != self.servid:
                self.parentserv.addItem(service['url'] +" - s#" + unicode(service['id']), QtCore.QVariant(service['id']))
        # Select good row
        index = self.parentserv.findText(parentserv, QtCore.Qt.MatchEndsWith)
        if index > -1:
            self.parentserv.setCurrentIndex(index)

    def completeMachine(self):
        index = self.machine.findText(self.machineline.text(), QtCore.Qt.MatchContains)
        if index == -1:
            msgBox = QtGui.QMessageBox(QtGui.QMessageBox.Critical, "No machine found","No machine found")
            msgBox.exec_();
            self.machine.setFocus()
        else:
            self.machine.setCurrentIndex(index)
        

    def completeParentserv(self):
        index = self.parentserv.findText(self.parentservline.text(), QtCore.Qt.MatchContains)
        if index == -1:
            index = 0
        self.parentserv.setCurrentIndex(index)

    def del_metadata(self, button):
        self.metadata[button.key].hide()
        button.key.hide()
        button.hide()
        self.metadata[button.key].destroy()
        del(self.metadata[button.key])

    def exec_(self):
        # get groups lists
        groups = listGroup()
        if not "list" in groups:
            return False
        for group in groups["list"]:
            ## ADD a checkbox to show/hide all groups/membre groups
            #if group["member"]:
            item = QtGui.QListWidgetItem(group['name'] +" - g#" + unicode(group['id']))
            item.setData(Qt.UserRole, QtCore.QVariant(group['id']))
            self.groups.addItem(item)
#                self.groups.addItem(group['name'] +" - g#" + unicode(group['id']), QtCore.QVariant(group['id']))
        if self.servid:
            # Fill fields for edit mode
            service = getService(self.servid, True)
            self.informations = service["services"][-1]
            ## Show informations
            self.url.setText(self.informations["url"])
            
            self.machineline.setText("m#" + str(self.informations["machine_id"]))
            if not self.informations["parent_service_id"]:
                self.parentservline.setText(self.tr("No parent"))
            else:
                self.parentservline.setText("s#" + str(self.informations["parent_service_id"]))
            # groups
            if self.informations["groups_list"]:
                for group in self.informations["groups_list"]:
                    item_list = self.groups.findItems(QtCore.QString(group[1] + " - "), QtCore.Qt.MatchStartsWith)
                    # Selected groups in listwidget
                    if len(item_list) > 0:
                        item_list[0].setSelected(True) 
            self.notes.setText(self.informations["notes"])
            # metadata
            if isinstance(self.informations["metadata"], dict):
                self.metadata = dict([ (QtGui.QLabel(key), QtGui.QLabel(value))
                                   for key, value in
                                 self.informations["metadata"].items() ])
            else:
                self.metadata = {}
            for i, data in enumerate(self.metadata.items()):
                key_label, value_label = data
                self.metadata_layout.addWidget(key_label, i + 1, 0)
                self.metadata_layout.addWidget(value_label, i + 1, 1)
                del_button = QtGui.QPushButton("-")
                del_button.adjustSize()
                w = del_button.height()
                del_button.setMaximumWidth(w)
                del_button.key = key_label
                temp_func = partial(self.del_metadata, del_button)
                self.connect(del_button, QtCore.SIGNAL("clicked()"), temp_func)
                self.metadata_layout.addWidget(del_button, i+1, 2)
            self.metadata_layout.addWidget(self.metadata_button,
                                            len(self.metadata) + 1,
                                            2)
            # get machine lists
            self.fillMachinesList()
            # get services lists
            self.fillServicesList()
            # Set mode and texts
            self.mode = "edit"
            self.setWindowTitle(self.tr("Edit service"))
        else:
            # just get lists for add service mode
            if self.machid:
                self.machineline.setText("m#" + str(self.machid))
            # get machine lists
            self.fillMachinesList()
            # get services lists
            self.fillServicesList()

        self.advanced_to_simple()
        self.show()

    def editService(self):
        # Buil dict to transmit to the vault
        service_info = {"machine_id": None,
                        "parent_service_id": None,
                        "url": None,
                        "group_ids": None,
                        "secret": None,
                        "notes": None,
                        }
        # Fill it
        service_info["machine_id"], bool = self.machine.itemData(self.machine.currentIndex()).toInt()
        service_info["parent_service_id"], bool = self.parentserv.itemData(self.parentserv.currentIndex()).toInt()
        service_info["url"] = unicode(self.url.text())
        # Groups update
        group_ids_item_list = self.groups.selectedIndexes()
        if len(group_ids_item_list) < 1:
            error = QtGui.QMessageBox(QtGui.QMessageBox.Critical, self.tr("No group selected"), self.tr("You have to select at least one group"))
            error.exec_()
            return False
        group_ids = []
        for group_id_item in group_ids_item_list:
            group_id, bool,= group_id_item.data(QtCore.Qt.UserRole).toInt()
            group_ids.append(group_id)

        service_info["secret"] = unicode(self.password.text())

        service_info["notes"] = unicode(self.notes.text())

        service_info["metadata"] = dict([(unicode(key.text()),
                                          unicode(value.text()))
                                    for key, value in self.metadata.items()])

        if self.mode == "add":
            # Add a new service
            addService(service_info["machine_id"],
                        service_info["parent_service_id"],
                        service_info["url"],
                        group_ids,
                        service_info["secret"],
                        service_info["notes"],
                        service_info["metadata"])
        elif self.mode == "edit":
            # Edit a service
            ## Group management
            old_groups = set([group[0] for group in self.informations["groups_list"]])
            new_groups = set(group_ids)
            ### add service to this groups
            for group_id in new_groups.difference(old_groups):
                pdialog = progressdialog.ProgressDialog(self.tr("Adding service in a group"),
                            self.tr("Please wait while adding service s#%s in group g#%s" % (self.servid, group_id)),
                            addServiceGroup, group_id, self.servid)
                ret = pdialog.run()
            ### remove service from this groups
            for group_id in old_groups.difference(new_groups):
                delServiceGroup(group_id, self.servid)
            ## Edit service info 
            editService(self.servid, service_info)
            ## Edit service passwd 
            if service_info["secret"] != '':
                editPassword(self.servid, service_info["secret"])
        else:
            print "ERROR ??"
            return False
        # reload tree
        self.parent.search(None)
        self.done(1)
