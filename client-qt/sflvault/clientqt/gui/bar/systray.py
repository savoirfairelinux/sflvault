#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
#    sflvault_qt/bar/systray.py 
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
from PyQt5 import QtCore, QtGui, QtWidgets
import re
from PyQt5.QtCore import Qt
import sflvault
from sflvault.client import SFLvaultClient
import shutil
import os
from sflvault.clientqt.images.qicons import *
from sflvault.clientqt.lib.auth import *


class Systray(QtWidgets.QSystemTrayIcon):
    def __init__(self, parent=None, ):
        QtWidgets.QSystemTrayIcon.__init__(self, parent)
        self.parent = parent
        self.setIcon(Qicons("sflvault_icon"))
        self.createActions()
        self.createTrayMenu()

    def createActions(self):
        """
            Create action for context menu
        """
        self.minimizeAction = QtWidgets.QAction(self.tr("Mi&nimize"), self)
        self.minimizeAction.triggered.connect(self.parent.hide)

        self.maximizeAction = QtWidgets.QAction(self.tr("Ma&ximize"), self)
        self.maximizeAction.triggered.connect(self.parent.showMaximized)

        self.restoreAction = QtWidgets.QAction(self.tr("&Restore"), self)
        self.restoreAction.triggered.connect(self.parent.showNormal)

        self.quitAction = QtWidgets.QAction(self.tr("&Quit"), self)
        self.quitAction.triggered.connect(self.parent.app.quit)

        self.activated.connect(self.hideShow)

    def hideShow(self, reason):
        """
            Hide or show application
        """
        # Only if it s a left clik
        if reason == QtWidgets.QSystemTrayIcon.Trigger:
            if self.parent.isVisible():
                state = self.parent.saveGeometry()
                self.parent.settings.setValue("SFLvault-qt4/binsavewindow", state)
                self.parent.hide()
            else:
                self.parent.show()
                geometry = self.parent.settings.value("SFLvault-qt4/binsavewindow")
                self.parent.restoreGeometry(geometry)

    def createTrayMenu(self):
        """
            Load context menu
        """
        self.trayIconMenu = QtWidgets.QMenu()
        self.trayIconMenu.addAction(self.minimizeAction)
        self.trayIconMenu.addAction(self.maximizeAction)
        self.trayIconMenu.addAction(self.restoreAction)
        self.trayIconMenu.addSeparator()
        self.trayIconMenu.addAction(self.quitAction)
        self.setContextMenu(self.trayIconMenu)
