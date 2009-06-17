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
        self.file = self.addMenu(self.tr("&File"))
        self.edit = self.addMenu(self.tr("&Edit"))
        self.display = self.addMenu(self.tr("&Display"))
        self.help = self.addMenu(self.tr("&Help"))
       
        # File

        ## New
        self.new = self.file.addMenu(self.tr("&New"))
        self.new.setStatusTip(self.tr("Create new item"))
        ### Customer
        self.newcust = self.new.addAction(self.tr("&Customer..."))
        self.newcust.setStatusTip(self.tr("Create a new customer"))
        self.newcust.setEnabled(0)
        ## Machine
        self.newmach = self.new.addAction(self.tr("&Machine..."))
        self.newmach.setStatusTip(self.tr("Create a new machine"))
        self.newmach.setEnabled(0)
        ## Service
        self.newserv = self.new.addAction(self.tr("&Service..."))
        self.newserv.setStatusTip(self.tr("Create a new service"))
        self.newserv.setEnabled(0)

        ## Connection
        self.connection = self.file.addAction(self.tr("&Connection"))
        self.connection.setStatusTip(self.tr("Connection to the vault"))
        ## Quit
        self.quit = self.file.addAction(self.tr("&Quit"))
        self.quit.setStatusTip(self.tr("Quit Sflvault-qt"))
 
        # Edit
        ## Protocols config
        self.protocols = self.edit.addAction(self.tr("&Protocols..."))
        self.protocols.setShortcut(self.tr("Ctrl+Shift+P"))
        self.protocols.setStatusTip(self.tr("Manage protocols"))
        self.protocols.setEnabled(0)

        ## Group management
        self.groups = self.edit.addAction(self.tr("&Groups..."))
        self.groups.setShortcut(self.tr("Ctrl+Shift+G"))
        self.groups.setStatusTip(self.tr("Manage groups"))
        self.groups.setEnabled(0)

        ## Users management
        self.users = self.edit.addAction(self.tr("&Users..."))
        self.users.setShortcut(self.tr("ctrl+shift+U"))
        self.users.setStatusTip(self.tr("Manage users"))
        self.users.setEnabled(0)

        ## Settings
        self.preferences = self.edit.addAction(self.tr("&Settings..."))
        self.preferences.setShortcut(self.tr("Ctrl+Shift+S"))
        self.preferences.setStatusTip(self.tr("Sflvault settings"))

        # Display
        ## Search
        self.search = self.display.addAction(self.tr("&Search"))
        self.search.setShortcut(self.tr("Ctrl+F"))
        self.search.setStatusTip(self.tr("Show/hide search dock"))
        self.search.setCheckable(True)

        ## Alias
        self.alias = self.display.addAction(self.tr("&Alias"))
        self.alias.setShortcut(self.tr("Ctrl+Alt+A"))
        self.alias.setStatusTip(self.tr("Show/hide alias dock"))
        self.alias.setCheckable(True)

        ## Customers
        self.cust = self.display.addAction(self.tr("&Customer"))
        self.cust.setShortcut(self.tr("Ctrl+Alt+C"))
        self.cust.setStatusTip(self.tr("Show/hide customer dock"))
        self.cust.setCheckable(True)

        ## Machine
        self.mach = self.display.addAction(self.tr("&Machine"))
        self.mach.setShortcut(self.tr("Ctrl+Alt+M"))
        self.mach.setStatusTip(self.tr("Show/hide machine dock"))
        self.mach.setCheckable(True)

        ## Service
        self.serv = self.display.addAction(self.tr("&Service"))
        self.serv.setShortcut(self.tr("Ctrl+Alt+S"))
        self.serv.setStatusTip(self.tr("Show/hide service dock"))
        self.serv.setCheckable(True)

        # Help
        ## Help
        self.sflvaulthelp = self.help.addAction(self.tr("Sflvault &help"))
        self.sflvaulthelp.setShortcut(self.tr("Ctrl+F1"))
        self.sflvaulthelp.setStatusTip(self.tr("Help for sflvault"))

        ## Language
        self.lang = self.help.addAction(self.tr("&Language"))
        self.lang.setStatusTip(self.tr("Choose your language"))

        ## About sflvault
        self.sflvaultabout = self.help.addAction(self.tr("&About Sflvault"))
        self.sflvaultabout.setStatusTip(self.tr("About Sflvault"))

        ## About sflvault-qt
        self.guiabout = self.help.addAction(self.tr("About Sflvault-QT"))
        self.guiabout.setStatusTip(self.tr("About Sflvault-QT"))

    def enableItems(self):
        """
            Active some menus
        """
        self.newcust.setEnabled(1)
        self.newmach.setEnabled(1)
        self.newserv.setEnabled(1)
        self.protocols.setEnabled(1)
        self.groups.setEnabled(1)
        self.users.setEnabled(1)
