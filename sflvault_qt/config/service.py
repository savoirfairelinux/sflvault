#!/usr/bin/env python
# -*- coding: UTF-8 -*-
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

from lib.auth import *


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
        if not "service" in service:
            return False
        # Set windows
        self.setIcon(QtGui.QMessageBox.Question)
        self.ok = self.addButton(QtGui.QMessageBox.Ok)
        self.cancel = self.addButton(QtGui.QMessageBox.Cancel)
        self.setText(self.tr("Do you want to delete %s" % service["service"]["url"]))

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
    def __init__(self, servid=False, parent=None):
        QtGui.QDialog.__init__(self, parent)
        self.parent = parent
        self.settings = self.parent.settings
        self.servid = servid
        self.machines = {}
        self.services = {}
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
        self.groups = QtGui.QComboBox()
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

        class getPasswordThread(QtCore.QThread):
            def __init__(self, servid, parent):
                QtCore.QThread.__init__(self, parent)
                self.parent = parent
                self.servid = servid

            def run(self):
                # Launch function
                ret = getPassword(self.servid)
                # Set password text from decoding
                self.parent.password.setText(ret)
                self.quit()
        
        class getMachinesThread(QtCore.QThread):
            def __init__(self, parent):
                QtCore.QThread.__init__(self, parent)
                self.parent = parent

            def run(self):
                # Launch function
                self.parent.machines = listMachine()
                self.quit()

        class getServicesThread(QtCore.QThread):
            def __init__(self, parent):
                QtCore.QThread.__init__(self, parent)
                self.parent = parent

            def run(self):
                # Launch function
                self.parent.services = listService()
                self.quit()

        # create thread
        self.passwordThread = getPasswordThread(self.servid, self)
        self.machinesThread = getMachinesThread(self)
        self.servicesThread = getServicesThread(self)

        self.machineline = self.machine.lineEdit()
        QtCore.QObject.connect(self.machineline, QtCore.SIGNAL("editingFinished()"), self.completeMachine)
        self.parentservline = self.parentserv.lineEdit()
        QtCore.QObject.connect(self.parentservline, QtCore.SIGNAL("editingFinished()"), self.completeParentserv)

        # SIGNALS
        self.connect(self.save, QtCore.SIGNAL("clicked()"), self, QtCore.SLOT("accept()"))
        self.connect(self.cancel, QtCore.SIGNAL("clicked()"), self, QtCore.SLOT("reject()"))
        # Show password when decode is finished
        QtCore.QObject.connect(self.passwordThread, QtCore.SIGNAL("finished()"), self.password.show)
        # Hide passwordprogressbar  when decode is finished
        QtCore.QObject.connect(self.passwordThread, QtCore.SIGNAL("finished()"), self.passwordProgress.hide)

        QtCore.QObject.connect(self.servicesThread, QtCore.SIGNAL("finished()"), self.fillServicesList)
        QtCore.QObject.connect(self.machinesThread, QtCore.SIGNAL("finished()"), self.fillMachinesList)

    def fillMachinesList(self):
        # Fill machine combo box
        for machine in self.machines["list"]:
            self.machine.addItem(machine['name'] +" - m#" + unicode(machine['id']), QtCore.QVariant(machine['id']))
        # Select good row
        index = self.machine.findText(self.machineline.text(), QtCore.Qt.MatchContains)
        if index > -1:
            self.machine.setCurrentIndex(index)

    def fillServicesList(self):
        # Fill service combo box
        self.parentserv.addItem(self.tr("No parent"), QtCore.QVariant(None))
        for service in self.services["list"]:
            # Doesn t add this item in possible parent list (if it s edit mode
            if service['id'] != self.servid:
                self.parentserv.addItem(service['url'] +" - s#" + unicode(service['id']), QtCore.QVariant(service['id']))
        # Select good row
        index = self.parentserv.findText(self.parentservline.text(), QtCore.Qt.MatchContains)
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
        for group in groups["list"]:
            if group["member"]:
                self.groups.addItem(group['name'] +" - g#" + unicode(group['id']), QtCore.QVariant(group['id']))
        if self.servid:
            # Fill fields for edit mode
            service = getService(self.servid)
            informations = service["service"]
            ## Show informations
            self.url.setText(informations["url"])
            self.machineline.setText("m#" + str(informations["machine_id"]))
            if not informations["parent_service_id"]:
                self.parentservline.setText(self.tr("No parent"))
            else:
                self.parentservline.setText("s#" + str(informations["parent_service_id"]))
            self.groups.setCurrentIndex(self.groups.findData(
                                QtCore.QVariant(informations["group_id"])))
            self.notes.setText(informations["notes"])
            ## launch threads
            # get machine lists
            self.machinesThread.start()
            # get services lists
            self.servicesThread.start()
            # launch password decode thread
            self.passwordThread.start()
            # Set mode and texts
            self.mode = "edit"
            self.setWindowTitle(self.tr("Edit service"))
        else:
            # just get lists for add service mode
            # get machine list
            self.machinesThread.start()
            # get services list
            self.servicesThread.start()

        self.show()

    def accept(self):
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
        service_info["group_ids"], bool = self.groups.itemData(self.groups.currentIndex()).toInt()
        service_info["secret"] = unicode(self.password.text())
        service_info["notes"] = unicode(self.notes.text())
        if self.mode == "add":
            # Add a new service
            addService(service_info["machine_id"], service_info["parent_service_id"],
                         service_info["url"], service_info["group_ids"],
                        service_info["secret"], service_info["notes"])
        elif self.mode == "edit":
            # Edit a service
            editService(self.servid, service_info)
            editPassword(self.servid, service_info["secret"])
        # reload tree
        self.parent.search(None)
        self.done(1)
