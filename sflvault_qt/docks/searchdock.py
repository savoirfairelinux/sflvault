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

class SearchDock(QtGui.QDockWidget):
    def __init__(self, parent=None, ):
        QtGui.QDockWidget.__init__(self, "Search items", parent)
        self.parent = parent
        self.search = Search()
        self.setWidget(self.search)

    def connection(self):
        self.search.updateGroup()


class Search(QtGui.QWidget):
    def __init__(self, parent=None, ):
        QtGui.QWidget.__init__(self, parent)
        self.parent = parent
#        global token

        # QlineEdits
        self.search = QtGui.QLineEdit()
        self.searchLabel = QtGui.QLabel(self.tr("Search"))
        self.protocol = QtGui.QLineEdit("ssh")
        self.protocolLabel = QtGui.QLabel(self.tr("Protocol"))
        self.type = QtGui.QLineEdit("service")
        self.typeLabel = QtGui.QLabel(self.tr("Type"))
        self.groups = QtGui.QComboBox()
        self.groupsLabel = QtGui.QLabel(self.tr("Groups"))

        # QGridLayout
        mainLayout = QtGui.QGridLayout()
        mainLayout.addWidget(self.searchLabel,0,0)
        mainLayout.addWidget(self.search,1,0)
        mainLayout.addWidget(self.protocolLabel,0,4)
        mainLayout.addWidget(self.protocol,1,4)
        mainLayout.addWidget(self.typeLabel,0,5)
        mainLayout.addWidget(self.type,1,5)
        mainLayout.addWidget(self.groupsLabel,0,6)
        mainLayout.addWidget(self.groups,1,6)

        # Geometries
        self.setWindowTitle(self.tr("Search"))

        # Show window
        self.setLayout(mainLayout)

        # Update group list
#        self.updateGroup()

    def updateGroup(self):
        """
            Update Groups list
        """
        self.groups.clear()
        # Add All
        id = QtCore.QVariant(None)
        self.groups.addItem(self.tr("All"), id)
        # Get all groups 
        grouplist = getGroupList()
        if grouplist:
            for group in grouplist:
                id = QtCore.QVariant(group["id"])
                self.groups.addItem(group["name"], id)
        # Resize comboBox
        self.groups.setSizeAdjustPolicy(QtGui.QComboBox.AdjustToContents)
