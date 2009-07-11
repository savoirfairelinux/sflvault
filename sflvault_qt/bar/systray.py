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
from images.qicons import *
from lib.auth import *


class Systray(QtGui.QSystemTrayIcon):
    def __init__(self, parent=None, ):
        QtGui.QSystemTrayIcon.__init__(self, parent)
        self.parent = parent
        self.setIcon(Qicons("sflvault_icon"))
        self.createActions()
        self.createTrayMenu()

    def createActions(self):
        """
            Create action for context menu
        """
        self.minimizeAction = QtGui.QAction(self.tr("Mi&nimize"), self)
        QtCore.QObject.connect(self.minimizeAction,
                QtCore.SIGNAL("triggered()"), self.parent, QtCore.SLOT("hide()"))

        self.maximizeAction = QtGui.QAction(self.tr("Ma&ximize"), self)
        QtCore.QObject.connect(self.maximizeAction,
                QtCore.SIGNAL("triggered()"), self.parent,
                QtCore.SLOT("showMaximized()"))

        self.restoreAction = QtGui.QAction(self.tr("&Restore"), self)
        QtCore.QObject.connect(self.restoreAction,
                QtCore.SIGNAL("triggered()"), self.parent,
                QtCore.SLOT("showNormal()"))

        self.quitAction = QtGui.QAction(self.tr("&Quit"), self)
        QtCore.QObject.connect(self.quitAction, QtCore.SIGNAL("triggered()"),
                self.parent.close)

        QtCore.QObject.connect(self, QtCore.SIGNAL("activated (QSystemTrayIcon::ActivationReason)"), self.hideShow)

    def hideShow(self, reason):
        """
            Hide or show application
        """
        # Only if it s a left clik
        if reason == QtGui.QSystemTrayIcon.Trigger:
            if self.parent.isVisible():
                self.parent.hide()
            else:
                self.parent.show()

    def createTrayMenu(self):
        """
            Load context menu
        """
        self.trayIconMenu = QtGui.QMenu()
        self.trayIconMenu.addAction(self.minimizeAction)
        self.trayIconMenu.addAction(self.maximizeAction)
        self.trayIconMenu.addAction(self.restoreAction)
        self.trayIconMenu.addSeparator()
        self.trayIconMenu.addAction(self.quitAction)
        self.setContextMenu(self.trayIconMenu)
