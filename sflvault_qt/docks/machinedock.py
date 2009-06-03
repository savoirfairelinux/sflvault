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


from auth import auth
token = auth.getAuth()

class MachineInfoDock(QtGui.QDockWidget):
    def __init__(self, parent=None, ):
        QtGui.QDockWidget.__init__(self, "Machine", parent)
        self.parent = parent
        self.machineInfo = MachineInfo()
        self.setWidget(self.machineInfo)
        global token

    def showInformations(self, id):
        """
            Show machines informations
        """
        print id
        if id:
            machine = token.vault.machine.get(token.authtok,id)
            self.machineInfo.name.setText(machine["machine"]["name"])
            self.machineInfo.ip.setText(machine["machine"]["ip"])
            self.machineInfo.fqdn.setText(machine["machine"]["fqdn"])
            self.machineInfo.location.setText(machine["machine"]["location"])
            self.machineInfo.notes.setText(machine["machine"]["notes"])
        else:
            self.machineInfo.name.clear()
            self.machineInfo.ip.clear()
            self.machineInfo.fqdn.clear()
            self.machineInfo.location.clear()
            self.machineInfo.notes.clear()
            


class MachineInfo(QtGui.QWidget):
    def __init__(self, parent=None, ):
        QtGui.QWidget.__init__(self, parent)
        self.parent = parent

        # QlineEdits
        self.name = QtGui.QLineEdit()
        self.nameLabel = QtGui.QLabel(self.tr("Name"))
        self.ip = QtGui.QLineEdit()
        self.ipLabel = QtGui.QLabel(self.tr("IP"))
        self.fqdn = QtGui.QLineEdit()
        self.fqdnLabel = QtGui.QLabel(self.tr("FQDN"))
        self.location = QtGui.QLineEdit()
        self.locationLabel = QtGui.QLabel(self.tr("Location"))
        self.notes = QtGui.QLineEdit()
        self.notesLabel = QtGui.QLabel(self.tr("Notes"))
#        self.groupslist = QtGui.QLineEdit()

        # QGridLayout
        mainLayout = QtGui.QGridLayout()
        mainLayout.addWidget(self.nameLabel,0,0)
        mainLayout.addWidget(self.name,0,1)
        mainLayout.addWidget(self.ipLabel,1,0)
        mainLayout.addWidget(self.ip,1,1)
        mainLayout.addWidget(self.fqdnLabel,2,0)
        mainLayout.addWidget(self.fqdn,2,1)
        mainLayout.addWidget(self.locationLabel,3,0)
        mainLayout.addWidget(self.location,3,1)
        mainLayout.addWidget(self.notesLabel,4,0)
        mainLayout.addWidget(self.notes,4,1)

        # Geometries
        self.setWindowTitle(self.tr("Machine Informations"))

        # Show window
        self.setLayout(mainLayout)

        
