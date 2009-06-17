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


class Config(QtCore.QSettings):
    def __init__(self, config_filename='/home/' + os.getenv( 'USER' ) + '/.sflvault/config', parent=None):
        QtCore.QSettings.__init__(self, config_filename, 0, parent)
        sHomeUser   = '/home/' + os.getenv( 'USER' ) + '/'
        self.parent = parent
        self.config_filename = config_filename
        self.checkConfig()

    def readConfig(self, group=None):
        """
            Return all values or values of specified group
        """
        if not group:
            ret = self.allKeys()
        else:
            self.beginGroup(group)
            ret = self.childKeys()
            self.endGroup()
        return ret

    def checkConfig(self):
        """
            Check config and write default items if need
        """
        if not self.contains("protocols/ssh"):
            self.beginGroup("protocols")
            self.setValue("ssh", QtCore.QVariant("SSH protocol"));
            self.endGroup()

        self.saveConfig()

    def saveConfig(self):
        self.sync()
