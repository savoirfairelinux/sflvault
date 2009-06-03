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

class MenuBar(QtGui.QMenuBar):
    def __init__(self, parent=None, ):
        QtGui.QMenuBar.__init__(self, parent)
        self.parent = parent
        self.file = self.addMenu(self.tr("File"))
        self.edit = self.addMenu(self.tr("Edit"))
        self.about = self.addMenu(self.tr("About"))
        
        # Protocols config
        self.protocols = self.edit.addAction(self.tr("Protocols"))
        self.protocols.setShortcut(self.tr("Ctrl+Shift+P"))
        self.protocols.setStatusTip(self.tr("Manage protocols"))

        # Group management
        self.groups = self.edit.addAction(self.tr("Groups"))
        self.groups.setShortcut(self.tr("Ctrl+Shift+G"))
        self.groups.setStatusTip(self.tr("Manage groups"))

        #self.groups = self.edit.addMenu(self.tr("Groups"))
