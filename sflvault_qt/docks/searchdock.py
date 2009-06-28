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

class SearchDock(QtGui.QDockWidget):
    def __init__(self, parent=None, ):
        QtGui.QDockWidget.__init__(self, parent)
        self.parent = parent
        self.search = Search()
        self.setWidget(self.search)
        self.setWindowTitle(self.tr("Search items"))
        ## Check visibility
        QtCore.QObject.connect(self, QtCore.SIGNAL("visibilityChanged (bool)"), self.parent.menubar.checkDockBoxes)

    def connection(self):
        self.search.updateGroup()


class Search(QtGui.QWidget):
    def __init__(self, parent=None, ):
        QtGui.QWidget.__init__(self, parent)
        self.parent = parent

        # QlineEdits
        self.search = QtGui.QLineEdit()
        self.searchLabel = QtGui.QLabel(self.tr("Search"))
        self.groups = QtGui.QComboBox()
        self.groupsLabel = QtGui.QLabel(self.tr("Groups"))

        # QGridLayout
        mainLayout = QtGui.QGridLayout()
        mainLayout.addWidget(self.searchLabel,0,0)
        mainLayout.addWidget(self.search,0,1)
        mainLayout.addWidget(self.groupsLabel,1,0)
        mainLayout.addWidget(self.groups,1,1)

        # Geometries
        self.setWindowTitle(self.tr("Search"))

        # Show window
        self.setLayout(mainLayout)


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
