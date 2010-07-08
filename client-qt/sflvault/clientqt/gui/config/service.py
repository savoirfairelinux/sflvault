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
from PyQt4 import QtCore, QtGui
import re
from PyQt4.QtCore import Qt
import sflvault
from sflvault.client import SFLvaultClient
import shutil
import os
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
        if not self.servid:
            self.mode = "add"
        else:
            self.mode = "edit"

        self.setMinimumWidth(500)

        # Load gui items
        groupbox = QtGui.QGroupBox()
        self.machineLabel = QtGui.QLabel(self.tr("Machine"))
        self.machine = QtGui.QComboBox()
        self.machine.setEditable(1)
        self.parentservLabel = QtGui.QLabel(self.tr("Parent service"))
        self.parentserv = QtGui.QComboBox()
        self.parentserv.setEditable(1)
        self.urlLabel = QtGui.QLabel(self.tr("Url"))
        self.url = QtGui.QLineEdit()
        self.groupsLabel = QtGui.QLabel(self.tr("Group"))
        #self.groups = QtGui.QComboBox()
        self.groups = QtGui.QListWidget(self)
        self.groups.setSelectionMode(QtGui.QAbstractItemView.MultiSelection)
        self.passwordLabel = QtGui.QLabel(self.tr("Password"))
        self.password = QtGui.QLineEdit()
        self.password.hide()
        self.passwordProgress = QtGui.QProgressBar()
        self.passwordProgress.setMinimum(0)
        self.passwordProgress.setMaximum(0)
        self.passwordProgress.hide()
        if self.mode == "edit":
            self.password.hide()
            self.passwordProgress.show()
        else:
            self.password.show()
            self.passwordProgress.hide()
        self.notesLabel = QtGui.QLabel(self.tr("Notes"))
        self.notes = QtGui.QLineEdit()

        self.save = QtGui.QPushButton(self.tr("Save service"))
        self.cancel = QtGui.QPushButton(self.tr("Cancel"))

        # Positionning items
        ## Groups groupbox
        gridLayout = QtGui.QGridLayout()
        gridLayout.addWidget(self.machineLabel, 1, 0)
        gridLayout.addWidget(self.machine, 1, 1)
        gridLayout.addWidget(self.parentservLabel, 2, 0)
        gridLayout.addWidget(self.parentserv, 2, 1)
        gridLayout.addWidget(self.urlLabel, 3, 0)
        gridLayout.addWidget(self.url, 3, 1)
        gridLayout.addWidget(self.groupsLabel, 4, 0)
        gridLayout.addWidget(self.groups, 4, 1)
        gridLayout.addWidget(self.passwordLabel, 5, 0)
        gridLayout.addWidget(self.password, 5, 1)
        gridLayout.addWidget(self.passwordProgress, 5, 1)
        gridLayout.addWidget(self.notesLabel, 6, 0)
        gridLayout.addWidget(self.notes, 6, 1)
        gridLayout.addWidget(self.save, 7, 0)
        gridLayout.addWidget(self.cancel, 7, 1)
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
        self.connect(self.save, QtCore.SIGNAL("clicked()"), self.editService)
        self.connect(self.cancel, QtCore.SIGNAL("clicked()"), self, QtCore.SLOT("reject()"))

    def fillPassword(self):
        decodedpassword = getPassword(self.servid)
        self.password.setText(decodedpassword)
        self.password.show()
        self.passwordProgress.hide()

    def fillMachinesList(self):
        machines = listMachine()
        # Fill machine combo box
        selected_machine = self.machineline.text()
        for machine in machines["list"]:
            self.machine.addItem(machine['name'] +" - m#" + unicode(machine['id']), QtCore.QVariant(machine['id']))
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

    def exec_(self):
        # get groups lists
        groups = listGroup()
        if not "list" in groups:
            return False
        for group in groups["list"]:
            if group["member"]:
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
            # get machine lists
            self.fillMachinesList()
            # get services lists
            self.fillServicesList()
            # launch password decode thread
            self.fillPassword()
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
        # groups update
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

        if self.mode == "add":
            # Add a new service
            addService(service_info["machine_id"], service_info["parent_service_id"],
                         service_info["url"], group_ids,
                        service_info["secret"], service_info["notes"])
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
            editPassword(self.servid, service_info["secret"])
        else:
            print "ERROR ??"
            return False
        # reload tree
        self.parent.search(None)
        self.done(1)
