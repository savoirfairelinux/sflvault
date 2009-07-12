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

class ServiceWidget(QtGui.QDialog):
    def __init__(self, servid=None, parent=None):
        QtGui.QDialog.__init__(self, parent)
        self.parent = parent
        self.settings = self.parent.settings
        self.servid = servid
        self.mode = "add"

        # Load gui items
        groupbox = QtGui.QGroupBox()
        self.machineLabel = QtGui.QLabel(self.tr("Machine"))
        self.machine = QtGui.QComboBox()
        self.parentservLabel = QtGui.QLabel(self.tr("Parent service"))
        self.parentserv = QtGui.QComboBox()
        self.urlLabel = QtGui.QLabel(self.tr("Url"))
        self.url = QtGui.QLineEdit()
        self.groupsLabel = QtGui.QLabel(self.tr("Group"))
        self.groups = QtGui.QComboBox()
        self.passwordLabel = QtGui.QLabel(self.tr("Password"))
        self.password = QtGui.QLineEdit()
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
        gridLayout.addWidget(self.notesLabel, 6, 0)
        gridLayout.addWidget(self.notes, 6, 1)
        gridLayout.addWidget(self.save, 7, 0)
        gridLayout.addWidget(self.cancel, 7, 1)
        groupbox.setLayout(gridLayout)

        mainLayout = QtGui.QGridLayout()
        mainLayout.addWidget(groupbox,0,0)
        self.setLayout(mainLayout)

        self.setWindowTitle(self.tr("Add service"))

        # SIGNALS
        self.connect(self.save, QtCore.SIGNAL("clicked()"), self, QtCore.SLOT("accept()"))
        self.connect(self.cancel, QtCore.SIGNAL("clicked()"), self, QtCore.SLOT("reject()"))

    def exec_(self):
        # get machine lists
        machines = listMachine()
        for machine in machines["list"]:
            self.machine.addItem(machine['name'] +" - m#" + unicode(machine['id']), QtCore.QVariant(machine['id']))
        # get groups lists
        groups = listGroup()
        for group in groups["list"]:
            if group["member"]:
                self.groups.addItem(group['name'] +" - g#" + unicode(group['id']), QtCore.QVariant(group['id']))
        # get services lists
        services = listService()
        self.parentserv.addItem(self.tr("No parent"), QtCore.QVariant(None))
        for service in services["list"]:
            self.parentserv.addItem(service['url'] +" - s#" + unicode(service['id']), QtCore.QVariant(service['id']))
        if self.servid:
            # Fill fields for edit mode
            service = getService(self.servid)
            informations = service["service"]
            self.url.setText(informations["url"])
            self.machine.setCurrentIndex(self.machine.findData(
                                QtCore.QVariant(informations["machine_id"])))
            self.groups.setCurrentIndex(self.groups.findData(
                                QtCore.QVariant(informations["group_id"])))
            if informations["parent_service_id"]:
                self.parentserv.setCurrentIndex(self.parentserv.findData(
                                    QtCore.QVariant(informations["parent_service_id"])))
            self.notes.setText(informations["notes"])
            password = getPassword(self.servid)
            self.password.setText(password)
            # Set mode and texts
            self.mode = "edit"
            self.setWindowTitle(self.tr("Edit service"))
        self.show()

    def accept(self):
        # Buil dict to transmit to the vault
        service_info = {"machine_id": None,
                        "parenr_service_id": None,
                        "url": None,
                        "group_ids": None,
                        "secret": None,
                        "notes": None,
                        }
        # Fill it
        service_info["machine_id"], bool = self.machine.itemData(self.machine.currentIndex()).toInt()
        service_info["parentservid"], bool = self.parentserv.itemData(self.parentserv.currentIndex()).toInt()
        service_info["url"] = unicode(self.url.text())
        service_info["group_ids"], bool = self.groups.itemData(self.groups.currentIndex()).toInt()
        service_info["secret"] = unicode(self.password.text())
        service_info["notes"] = unicode(self.notes.text())
        if self.mode == "add":
            # Add a new service
            addService(service_info["machine_id"], service_info["parentservid"],
                         service_info["url"], service_info["group_ids"],
                        service_info["secret"], service_info["notes"])
        elif self.mode == "edit":
            # Edit a service
            editService(self.servid, service_info)
        # reload tree
        self.parent.search(None)
        self.done(1)
