#!/usr/bin/env python
# -*- coding: UTF-8 -*-
#
#    sflvault_qt/config/config.py
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
import platform


class Config(QtCore.QSettings):
    def __init__(self, parent=None):
        if platform.system() == 'Windows':
            QtCore.QSettings.__init__(self, QtCore.QSettings.IniFormat,
                                        QtCore.QSettings.UserScope,
                                        "SFLvault", "config", parent);
        else:
            QtCore.QSettings.__init__(self,
                         '/home/' + os.getenv( 'USER' ) + '/.sflvault/config',
                         0, parent)
        self.parent = parent
        self.checkConfig()

    def readConfig(self, group=None):
        """
            Return all values or values of specified group
        """
        if not group:
            ret = self.allKeys()
        else:
            self.beginGroup(group)
            if group == "protocols":
                ret = self.childGroups()
            else:
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
