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
    def __init__(self, macjid=None, parent=None):
        QtGui.QDialog.__init__(self, parent)
        self.parent = parent
        self.settings = self.parent.settings
        self.protocols = {}

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

        self.save = QtGui.QPushButton(self.tr("Add machine"))
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

        self.setWindowTitle(self.tr("Add machine"))

        # SIGNALS
        self.connect(self.save, QtCore.SIGNAL("clicked()"), self, QtCore.SLOT("accept()"))
        self.connect(self.cancel, QtCore.SIGNAL("clicked()"), self, QtCore.SLOT("reject()"))

    def exec_(self):
        # get machine lists
        machines = listMachine()
        for machine in machines["list"]:
            self.machine.addItem(machine['name'] +" - m#" + unicode(machine['id']) , QtCore.QVariant(machine['id']))
        # get groups lists
        groups = listGroup()
        for group in groups["list"]:
            if group["member"]:
                self.groups.addItem(group['name'] +" - g#" + unicode(group['id']) , QtCore.QVariant(group['id']))
        # get services lists
#        services = listService()
#        for service in services["list"]:
#            self.parentserv.addItem(service['name'] +" - s#" + unicode(service['id']) , QtCore.QVariant(service['id']))
        self.show()

    def accept(self):
        machid, bool = self.machine.itemData(self.machine.currentIndex()).toInt()
        parentservid, bool = self.parentserv.itemData(self.parentserv.currentIndex()).toInt()
        url = unicode(self.url.text())
        groupids, bool = self.groups.itemData(self.groups.currentIndex()).toInt()
        password = unicode(self.password.text())
        notes = unicode(self.notes.text())
        addService(machid, parentservid, url, groupids, password, notes)
        self.parent.search(None)
        self.done(1)
