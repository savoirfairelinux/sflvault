#!/usr/bin/env python
# -*- coding: UTF-8 -*-
#
#    sflvault_qt/bar/menubar.py
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

class MenuBar(QtGui.QMenuBar):
    def __init__(self, parent=None, ):
        QtGui.QMenuBar.__init__(self, parent)
        self.parent = parent
        self.file_ = self.addMenu(self.tr("&File"))
        self.edit = self.addMenu(self.tr("&Edit"))
        self.display = self.addMenu(self.tr("&Display"))
        self.tools = self.addMenu(self.tr("&Tools"))
        self.help_ = self.addMenu(self.tr("&Help"))
       
        # File
        ## New
        self.new = self.file_.addMenu(self.tr("&New"))
        self.new.setStatusTip(self.tr("Create new item"))
        ### Customer
        self.newcust = self.new.addAction(self.tr("&Customer..."))
        self.newcust.setStatusTip(self.tr("Create a new customer"))
        self.newcust.setEnabled(0)
        ### Machine
        self.newmach = self.new.addAction(self.tr("&Machine..."))
        self.newmach.setStatusTip(self.tr("Create a new machine"))
        self.newmach.setEnabled(0)
        ### Service
        self.newserv = self.new.addAction(self.tr("&Service..."))
        self.newserv.setStatusTip(self.tr("Create a new service"))
        self.newserv.setEnabled(0)


        ## Connection
        self.connection = self.file_.addAction(self.tr("&Connect to the vault"))
        self.connection.setStatusTip(self.tr("Connect to the vault"))
        ## Quick Connection
        self.quickconnect = self.file_.addAction(self.tr("&Quick Connect..."))
        self.quickconnect.setShortcut(self.tr("Ctrl+O"))
        self.quickconnect.setStatusTip(self.tr("Connect to a service..."))
        self.quickconnect.setEnabled(0)
        ## Quit
        self.quit = self.file_.addAction(self.tr("&Quit"))
        self.quit.setStatusTip(self.tr("Quit Sflvault-qt"))
 
        # Edit
        ## Protocols config
        self.protocols = self.edit.addAction(self.tr("&Protocols..."))
        self.protocols.setStatusTip(self.tr("Manage protocols"))
        self.protocols.setEnabled(0)

        ## Users management
        self.users = self.edit.addAction(self.tr("&Users..."))
        self.users.setShortcut(self.tr("Ctrl+U"))
        self.users.setStatusTip(self.tr("Manage users"))
        self.users.setEnabled(0)

        ## Settings
        self.preferences = self.edit.addAction(self.tr("&Settings..."))
        self.preferences.setStatusTip(self.tr("Sflvault settings"))

        ## Set settings file
#        self.configfile = self.edit.addAction(self.tr("Set settings &File..."))
#        self.configfile.setStatusTip(self.tr("Set Sflvault settings file"))

        # Display
        self.listDockBoxes = {}
        ## Search
        self.search = self.display.addAction(self.tr("&Search"))
        self.search.setShortcut(self.tr("Ctrl+Alt+S"))
        self.search.setStatusTip(self.tr("Show/hide search dock"))
        self.search.setCheckable(True)
        self.listDockBoxes['search'] = self.search
        ## Alias
        self.alias = self.display.addAction(self.tr("&Alias"))
        self.alias.setShortcut(self.tr("Ctrl+Alt+A"))
        self.alias.setStatusTip(self.tr("Show/hide alias dock"))
        self.alias.setCheckable(True)
        self.listDockBoxes['alias'] = self.alias
        ## Info
        self.info = self.display.addAction(self.tr("&Informations"))
        self.info.setShortcut(self.tr("Ctrl+Alt+I"))
        self.info.setStatusTip(self.tr("Show/hide information dock"))
        self.info.setCheckable(True)
        self.listDockBoxes['info'] = self.info

        self.checkDockBoxes()

        # Tools
        ## save password in wallet
        self.savepass = self.tools.addAction(self.tr("&Save password"))
        self.savepass.setStatusTip(self.tr("Save your password in your wallet"))
        ## First Connection
        self.firstconnection = self.tools.addAction(self.tr("&First connection to the vault"))
        self.firstconnection.setStatusTip(self.tr("Initialize your vault account"))


        # Help
        ## Help
        self.sflvaulthelp = self.help_.addAction(self.tr("Sflvault &help"))
        self.sflvaulthelp.setShortcut(self.tr("Ctrl+F1"))
        self.sflvaulthelp.setStatusTip(self.tr("Help for sflvault"))

        ## About sflvault
        self.sflvaultabout = self.help_.addAction(self.tr("&About Sflvault"))
        self.sflvaultabout.setStatusTip(self.tr("About Sflvault"))

        ## About sflvault-qt
        self.guiabout = self.help_.addAction(self.tr("About Sflvault-QT"))
        self.guiabout.setStatusTip(self.tr("About Sflvault-QT"))

    def enableItems(self):
        """
            Active some menus
        """
        self.newcust.setEnabled(1)
        self.newmach.setEnabled(1)
        self.newserv.setEnabled(1)
        self.protocols.setEnabled(1)
        self.users.setEnabled(1)
        self.quickconnect.setEnabled(1)

    def checkDockBoxes(self):
        """
            Check box if dock is visible
        """
        for name, widget in self.parent.listWidget.iteritems():
            if widget.isVisible():
                self.listDockBoxes[name].setChecked(True)
            else:
                self.listDockBoxes[name].setChecked(False)
