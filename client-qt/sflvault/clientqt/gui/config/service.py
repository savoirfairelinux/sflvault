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

from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtCore import Qt

import sflvault
from sflvault.client import SFLvaultClient
from sflvault.clientqt.gui.dialog import progressdialog
from sflvault.clientqt.lib.auth import *


class DeleteServiceWidget(QtWidgets.QMessageBox):
    def __init__(self, servid=None, parent=None):
        QtWidgets.QMessageBox.__init__(self, parent)
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
        self.setIcon(QtWidgets.QMessageBox.Question)
        self.ok = self.addButton(QtWidgets.QMessageBox.Ok)
        self.cancel = self.addButton(QtWidgets.QMessageBox.Cancel)
        self.setText(self.tr("Do you want to delete %s" % service["services"][-1]["url"]))

        # SIGNALS
        self.ok.clicked.connect(self.accept)
        self.cancel.clicked.connect(self.reject)

    def accept(self):
        # Delete service
        status = delService(self.servid)
        if status:
            # reload tree
            self.parent.search(None)
            self.done(1)


class EditServiceWidget(QtWidgets.QDialog):
    def __init__(self, servid=False, machid=None, parent=None):
        QtWidgets.QDialog.__init__(self, parent)
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
        groupbox = QtWidgets.QGroupBox()
        groupbox.setTitle(self.tr("Service"))

        # Service info groupbox
        info_layout = QtWidgets.QGridLayout()
        groupbox_info = QtWidgets.QGroupBox()
        groupbox_info.setTitle(self.tr("Service info"))
        groupbox_info.setLayout(info_layout)
        self.machineLabel = QtWidgets.QLabel(self.tr("Machine"))
        self.machineLabel.setMinimumWidth(100)
        self.machine = QtWidgets.QComboBox()
        self.machine.setEditable(1)
        self.parentservLabel = QtWidgets.QLabel(self.tr("Parent service"))
        self.parentservLabel.setMinimumWidth(100)
        self.parentserv = QtWidgets.QComboBox()
        self.parentserv.setEditable(1)
        self.groupsLabel = QtWidgets.QLabel(self.tr("Group"))
        self.groupsLabel.setMinimumWidth(100)
        self.groups = QtWidgets.QListWidget(self)
        self.groups.setSelectionMode(QtWidgets.QAbstractItemView.MultiSelection)
        self.notesLabel = QtWidgets.QLabel(self.tr("Notes"))
        self.notesLabel.setMinimumWidth(100)
        self.notes = QtWidgets.QLineEdit()
        info_layout.addWidget(self.machineLabel, 0, 0)
        info_layout.addWidget(self.machine, 0, 1)
        info_layout.addWidget(self.parentservLabel, 1, 0)
        info_layout.addWidget(self.parentserv, 1, 1)
        info_layout.addWidget(self.groupsLabel, 2, 0)
        info_layout.addWidget(self.groups, 2, 1)
        info_layout.addWidget(self.notesLabel, 3, 0)
        info_layout.addWidget(self.notes, 3, 1)

        # Metadata groupbox
        self.metadata_layout = QtWidgets.QGridLayout()
        self.groupbox_metadata = QtWidgets.QGroupBox()
        self.groupbox_metadata.setTitle(self.tr("Metadata"))
        self.groupbox_metadata.setLayout(self.metadata_layout)
        self.metadata_key_label = QtWidgets.QLabel(self.tr("Metadata key"))
        self.metadata_value_label = QtWidgets.QLabel(self.tr("Metadata value"))
        self.metadata_button = QtWidgets.QPushButton(self.tr("+"))
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
        url_layout = QtWidgets.QGridLayout()
        groupbox_url = QtWidgets.QGroupBox()
        groupbox_url.setTitle(self.tr("Url"))
        groupbox_url.setLayout(url_layout)
        self.usernameLabel = QtWidgets.QLabel(self.tr("Username"))
        self.usernameLabel.setMinimumWidth(100)
        self.username = QtWidgets.QLineEdit()
        self.hostLabel = QtWidgets.QLabel(self.tr("Host"))
        self.hostLabel.setMinimumWidth(100)
        self.host = QtWidgets.QLineEdit()
        self.portLabel = QtWidgets.QLabel(self.tr("Port"))
        self.portLabel.setMinimumWidth(100)
        self.port = QtWidgets.QLineEdit()
        self.schemeLabel = QtWidgets.QLabel(self.tr("Scheme"))
        self.scheme = QtWidgets.QLineEdit()
        self.paramsLabel = QtWidgets.QLabel(self.tr("Parameters"))
        self.paramsLabel.setMinimumWidth(100)
        self.params = QtWidgets.QLineEdit()
        self.urlLabel = QtWidgets.QLabel(self.tr("Url"))
        self.urlLabel.setMinimumWidth(100)
        self.urlLabel.hide()
        self.url = QtWidgets.QLineEdit()
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
        password_layout = QtWidgets.QGridLayout()
        groupbox_password = QtWidgets.QGroupBox()
        groupbox_password.setTitle(self.tr("Secret"))
        groupbox_password.setLayout(password_layout)
        self.passwordLabel = QtWidgets.QLabel(self.tr("Password"))
        self.passwordLabel.setMaximumWidth(100)
        self.password = QtWidgets.QLineEdit()
        self.password_button = QtWidgets.QPushButton(self.tr("Show Password"))
        if self.mode == "edit":
            self.password.setReadOnly(1)
            self.password.setDisabled(1)
        else:
            self.password.setReadOnly(0)
            self.password.setEchoMode(QtWidgets.QLineEdit.Password)
        password_layout.addWidget(self.passwordLabel, 0, 0)
        password_layout.addWidget(self.password, 0, 1, 1, 2)
        password_layout.addWidget(self.password_button, 0, 3)

        # Button Groupbox
        button_layout = QtWidgets.QHBoxLayout()
        groupbox_button = QtWidgets.QGroupBox()
        groupbox_button.setLayout(button_layout)
        self.advanced = QtWidgets.QPushButton(self.tr("Advanced"))
        self.save = QtWidgets.QPushButton(self.tr("Save service"))
        self.cancel = QtWidgets.QPushButton(self.tr("Cancel"))
        button_layout.addWidget(self.cancel)
        button_layout.addWidget(self.advanced)
        button_layout.addWidget(self.save)

        # Positionning items
        # Main groupbox
        gridLayout = QtWidgets.QGridLayout()
        gridLayout.addWidget(groupbox_url, 1, 0, 1, 2)
        gridLayout.addWidget(groupbox_info, 2, 0, 1, 2)
        gridLayout.addWidget(groupbox_password, 6, 0, 1, 2)
        gridLayout.addWidget(groupbox_button, 7, 0, 1, 2)
        groupbox.setLayout(gridLayout)
        mainLayout = QtWidgets.QGridLayout()
        mainLayout.addWidget(groupbox,0,0)
        self.setLayout(mainLayout)

        self.setWindowTitle(self.tr("Add service"))

        self.machineline = self.machine.lineEdit()
        self.machineline.editingFinished.connect(self.completeMachine)
        self.parentservline = self.parentserv.lineEdit()
        self.parentservline.editingFinished.connect(self.completeParentserv)

        # SIGNALS
        self.username.textEdited.connect(self.simple_to_advanced)
        self.host.textEdited.connect(self.simple_to_advanced)
        self.port.textEdited.connect(self.simple_to_advanced)
        self.scheme.textEdited.connect(self.simple_to_advanced)
        self.params.textEdited.connect(self.simple_to_advanced)
        self.url.textEdited.connect(self.advanced_to_simple)
        self.password_button.clicked.connect(self.fill_password)

        self.metadata_button.clicked.connect(self.add_metadata)

        self.advanced.clicked.connect(self.switch_edit)
        self.save.clicked.connect(self.editService)
        self.cancel.clicked.connect(self.reject)

    def add_metadata(self):
        key, ret = QtWidgets.QInputDialog.getText(self,
                                            self.tr("New Metadata"),
                                            self.tr("Metadata key:"),
                                            QtWidgets.QLineEdit.Normal,
                                            '');
        if key == '':
            print("error")
        else:
            value, ret = QtWidgets.QInputDialog.getText(self,
                                            self.tr("New Metadata"),
                                            self.tr("Metadata value:"),
                                            QtWidgets.QLineEdit.Normal,
                                            '');
            if value == '':
                print("error")
            key_label = QtWidgets.QLabel(key)
            value_label = QtWidgets.QLabel(value)

            self.metadata[key_label] = value_label

            length = self.metadata_layout.count()
            self.metadata_layout.addWidget(key_label, length, 0)
            self.metadata_layout.addWidget(value_label, length, 1)
            self.metadata_layout.addWidget(self.metadata_button, length + 1, 2)
            del_button = QtWidgets.QPushButton("-")
            del_button.adjustSize()
            w = del_button.height()
            del_button.setMaximumWidth(w)
            del_button.key = key_label 
            temp_func = partial(self.del_metadata, del_button)
            del_button.clicked.connect(temp_func)
            self.metadata_layout.addWidget(del_button, length, 2)


    def switch_edit(self):
        if self.advanced.text() == str(self.tr("Advanced")):
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
        advanced_url = str(self.url.text())
        # Split data
        if len(advanced_url.split("@")) > 2:
            temp = advanced_url.rsplit("@",1)
            username = temp[0].split("://")[-1]
            protocol = temp[0].split("://")[0]
            url = temp[1]
            url = QtCore.QUrl(protocol + "://" + url)
        else:
            url = QtCore.QUrl(advanced_url)
        username = str(url.userName())
        protocol = str(url.scheme())
        port = str(url.port() if url.port() > 0 else '')
        host = str(url.host())
        uri = str(url.path())
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
        try:
            advanced_url.setPort(int(port) if port else -1)
        except ValueError:
            advanced_url.setPort(-1)
        advanced_url.setPath(params)
        advanced_url.setUserName(username)
        self.url.setText(advanced_url.toString())

    def fill_password(self):
        if self.mode == "edit":
            decodedpassword = getPassword(self.servid)
            if decodedpassword != False:
                self.password.setText(decodedpassword)
                self.password.setEchoMode(QtWidgets.QLineEdit.Normal)
                self.password.setReadOnly(0)
                self.password.setDisabled(0)
            else:
                # TODO show error box (permission denied ?)
                pass
        else:
            if self.password.echoMode() == QtWidgets.QLineEdit.Password:
                self.password_button.setText(self.tr("Hide Password"))
                self.password.setEchoMode(QtWidgets.QLineEdit.Normal)
            else:
                self.password_button.setText(self.tr("Show Password"))
                self.password.setEchoMode(QtWidgets.QLineEdit.Password)


    def fillMachinesList(self):
        machines = listMachine()
        # Fill machine combo box
        selected_machine = self.machineline.text()
        for machine in machines["list"]:
            self.machine.addItem(machine['name'] + " - m#" + str(machine['id']), machine['id'])
        # Select good row
        index = self.machine.findText(" - " + selected_machine, QtCore.Qt.MatchEndsWith)
        if index > -1:
            self.machine.setCurrentIndex(index)

    def fillServicesList(self):
        parentserv = self.parentservline.text()
        services = listService()
        # Fill service combo box
        self.parentserv.addItem(self.tr("No parent"), None)
        for service in services["list"]:
            # Doesn t add this item in possible parent list (if it s edit mode
            if service['id'] != self.servid:
                self.parentserv.addItem(service['url'] +" - s#" + str(service['id']), service['id'])
        # Select good row
        index = self.parentserv.findText(parentserv, QtCore.Qt.MatchEndsWith)
        if index > -1:
            self.parentserv.setCurrentIndex(index)

    def completeMachine(self):
        index = self.machine.findText(self.machineline.text(), QtCore.Qt.MatchContains)
        if index == -1:
            msgBox = QtWidgets.QMessageBox(QtWidgets.QMessageBox.Critical, "No machine found","No machine found")
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
            item = QtWidgets.QListWidgetItem(group['name'] +" - g#" + str(group['id']))
            item.setData(Qt.UserRole, group['id'])
            self.groups.addItem(item)
#                self.groups.addItem(group['name'] +" - g#" + str(group['id']), QtCore.QVariant(group['id']))
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
                    item_list = self.groups.findItems(str(group[1] + " - "), QtCore.Qt.MatchStartsWith)
                    # Selected groups in listwidget
                    if len(item_list) > 0:
                        item_list[0].setSelected(True) 
            self.notes.setText(self.informations["notes"])
            # metadata
            if isinstance(self.informations["metadata"], dict):
                self.metadata = dict([ (QtWidgets.QLabel(key), QtWidgets.QLabel(value))
                                   for key, value in
                                 self.informations["metadata"].items() ])
            else:
                self.metadata = {}
            for i, data in enumerate(self.metadata.items()):
                key_label, value_label = data
                self.metadata_layout.addWidget(key_label, i + 1, 0)
                self.metadata_layout.addWidget(value_label, i + 1, 1)
                del_button = QtWidgets.QPushButton("-")
                del_button.adjustSize()
                w = del_button.height()
                del_button.setMaximumWidth(w)
                del_button.key = key_label
                temp_func = partial(self.del_metadata, del_button)
                del_button.clicked.connect(temp_func)
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
        service_info["machine_id"] = self.machine.itemData(self.machine.currentIndex())
        service_info["parent_service_id"] = self.parentserv.itemData(self.parentserv.currentIndex())
        service_info["url"] = str(self.url.text())
        # Groups update
        group_ids_item_list = self.groups.selectedIndexes()
        if len(group_ids_item_list) < 1:
            error = QtWidgets.QMessageBox(QtWidgets.QMessageBox.Critical, self.tr("No group selected"), self.tr("You have to select at least one group"))
            error.exec_()
            return False
        group_ids = []
        for group_id_item in group_ids_item_list:
            group_ids.append(int(group_id_item.data(QtCore.Qt.UserRole)))

        service_info["secret"] = str(self.password.text())

        service_info["notes"] = str(self.notes.text())

        service_info["metadata"] = dict([(str(key.text()),
                                          str(value.text()))
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
            print("ERROR ??")
            return False
        # reload tree
        self.parent.search(None)
        self.done(1)
