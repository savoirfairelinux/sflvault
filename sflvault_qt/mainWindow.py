#!/usr/bin/env python
# -*- coding: UTF-8 -*-

import sys
from PyQt4 import QtCore, QtGui
import re
from PyQt4.QtCore import Qt
import sflvault
from tree.tree import TreeVault, TreeView
from docks.infodock import InfoDock
from docks.searchdock import SearchDock
from docks.aliasdock import AliasDock
from config.protocols import ProtocolsWidget
from config.groups import GroupsWidget
from config.preferences import PreferencesWidget
from config.config import Config
from bar.menubar import MenuBar
from bar.systray import Systray
from sflvault.client import SFLvaultClient
import shutil
import os
from lib.error import *
from lib.auth import *


class MainWindow(QtGui.QMainWindow):
    def __init__(self, parent=None):
        QtGui.QMainWindow.__init__(self, parent)
        self.parent = parent
        self.listWidget = {}

        # Load settings
        self.settings = Config(parent=self)

        # Load GUI item
        self.treewidget = TreeVault(parent=self)
        self.tree = self.treewidget.tree
        self.aliasdock = AliasDock(parent=self)
        self.aliasdock.setObjectName("aliases")
        self.searchdock = SearchDock(parent=self)
        self.searchdock.setObjectName("search")
        self.infodock = InfoDock(parent=self)
        self.infodock.setObjectName("info")
        self.menubar = MenuBar(parent=self)
        self.systray = Systray(parent=self)

        # Create clipboard
        self.clipboard = QtGui.QApplication.clipboard()

        # Load alias list
        self.alias_list = self.aliasdock.alias.alias_list

        # Attach items to mainwindow
        self.setCentralWidget(self.treewidget)
        self.addDockWidget(QtCore.Qt.LeftDockWidgetArea,self.aliasdock)
        self.addDockWidget(QtCore.Qt.RightDockWidgetArea,self.searchdock)
        self.addDockWidget(QtCore.Qt.RightDockWidgetArea,self.infodock)
        self.setMenuBar(self.menubar)

        # Read aliases
        self.aliasdock.readAliases()

        # Load windows
        self.protocols = ProtocolsWidget(parent=self)
        self.groups = GroupsWidget(parent=self)
        self.preferences = PreferencesWidget(parent=self)
        # Load shortcut
        self.setShortcut()

        # Signals
        ## Quit
        QtCore.QObject.connect(self.menubar.quit, QtCore.SIGNAL("triggered()"), self.close)
        ## Protocols
        QtCore.QObject.connect(self.menubar.protocols, QtCore.SIGNAL("triggered()"), self.protocols.exec_)
        ## Protocols
        QtCore.QObject.connect(self.menubar.quickconnect, QtCore.SIGNAL("triggered()"), self.quickConnection)
        ## Groups
        QtCore.QObject.connect(self.menubar.groups, QtCore.SIGNAL("triggered()"), self.groups.exec_)
        ## Vault connection
        QtCore.QObject.connect(self.menubar.connection, QtCore.SIGNAL("triggered()"), self.vaultConnection)
        ## Preferences
        QtCore.QObject.connect(self.menubar.preferences, QtCore.SIGNAL("triggered()"), self.preferences.exec_)


    def closeEvent(self, event):
        if self.settings.value("SFLvault-qt4/savewindow").toInt()[0] == QtCore.Qt.Checked:
            state = QtCore.QVariant(self.saveState())
            self.settings.setValue("SFLvault-qt4/binsavewindow", state)

    def search(self, research):
        """
            Search item in sflvault
        """
        # Get select group
        groups,bool = self.searchdock.search.groups.itemData(self.searchdock.search.groups.currentIndex()).toInt()
        if not bool:
            groups = None
        # Get research
        research = unicode(self.searchdock.search.search.text(), "latin-1").split(" ")
        self.tree.search(research, groups)

    def showInformations(self, index):
        """
           Show informations
        """
        # Get Id colunm
        indexId = self.tree.selectedIndexes()[1]

        # Check if selected item is an customer, machine or service
        if index.parent().isValid():
            # Selected item is a machine or service
            if index.parent().parent().isValid():
                # Selected item is a service
                # Get service parent id (machineid)
                parentIndex = self.tree.proxyModel.parent(index)
                # Get column 1 (id column)
                parentIndex1 = self.tree.proxyModel.index(parentIndex.row(), 1, parentIndex.parent())
                idmach = self.tree.proxyModel.data(parentIndex1, QtCore.Qt.DisplayRole).toString()
                idmach = int(idmach.split("#")[1])
                # Get machine parent id (customerid)
                parentIndex = self.tree.proxyModel.parent(parentIndex)
                parentIndex1 = self.tree.proxyModel.index(parentIndex.row(), 1, parentIndex.parent())
                idcust = self.tree.proxyModel.data(parentIndex1, QtCore.Qt.DisplayRole).toString()
                idcust = int(idcust.split("#")[1])
                # Get service id 
                idserv = indexId.data(QtCore.Qt.DisplayRole).toString()
                idserv = int(idserv.split("#")[1])
            else:
                # Selected item is a machine
                # Get machine parent id (customerid)
                parentIndex = self.tree.proxyModel.parent(index)
                parentIndex1 = self.tree.proxyModel.index(parentIndex.row(), 1, parentIndex.parent())
                idcust = self.tree.proxyModel.data(parentIndex1, QtCore.Qt.DisplayRole).toString()
                idcust = int(idcust.split("#")[1])
                # Get machine id 
                idmach = indexId.data(QtCore.Qt.DisplayRole).toString()
                idmach = int(idmach.split("#")[1])
                idserv = None
        else:
            # Selected item is a customer
            idcust = indexId.data(QtCore.Qt.DisplayRole).toString()
            idcust = int(idcust.split("#")[1])
            idmach = None
            idserv = None
        
        self.infodock.showInformations(idcust, machineid=idmach, serviceid=idserv)

    def GetIdByTree(self, index):
        """
            Get selected item id in tree and launch connection
        """
        # Get Id colunm
        indexId = self.tree.selectedIndexes()[1]
        idserv = indexId.data(QtCore.Qt.DisplayRole).toString()
        idserv = int(idserv.split("#")[1])
        # Check if seleted item is a service
        if index.parent().parent().isValid():
            self.connection(idserv)

    def GetIdByBookmark(self, index):
        """
            Get selected item id in bookmark and launch connection
        """
        # Get Id colunm
        indexId = self.alias_list.selectedIndexes()[1]
        idserv = indexId.data(QtCore.Qt.DisplayRole).toString()
        idserv = int(idserv.split("#")[1])
        # Check if seleted item is a service
        self.connection(idserv)

    def connection(self, idserv):
        """
            Connect to a service
        """
        # Get Options
        options = {}

        service = getService(idserv)
        if not service:
            return False
        # Copy password to clipboard
        self.passtoclip(idserv)

        url = service["service"]["url"]
        protocol, address = url.split("://")
        if self.settings.value("protocols/" + protocol):
            options["user"], options["address"] = address.split("@", 1)
            options["id"] = service["service"]["id"]
            options["vaultconnect"] = "sflvault connect %s" % options["id"]

            # Create Command
            command = unicode(self.settings.value("protocols/" + protocol).toString())
            print command
            command = command % options
            print command
            # Launch process
            self.procxterm = QtCore.QProcess()
            self.procxterm.start(command)

    def passtoclip(self, serviceid):
        """
            Paste password to the clipboard
        """
        self.clipboard.setText(getPassword(serviceid))

    def vaultConnection(self):
        """
            Connect to the vault
        """
        token = getAuth()
        if not token:
            return False

        ## "Connect" Alias
        QtCore.QObject.connect(self.aliasdock.alias.alias_list, QtCore.SIGNAL("doubleClicked (const QModelIndex&)"), self.GetIdByBookmark) 

        # "Connect" search dock
        ## Update Group list in search box
        self.searchdock.connection()

        # "Connect" tree
        ## Tree Search
        QtCore.QObject.connect(self.searchdock.search.search, QtCore.SIGNAL("textEdited (const QString&)"), self.search)
        ## Tree filter by groups
        QtCore.QObject.connect(self.searchdock.search.groups, QtCore.SIGNAL("currentIndexChanged (const QString&)"), self.search)
        self.tree.search(None, None)
        ## Tree bookmark
        QtCore.QObject.connect(self.tree.bookmarkAct, QtCore.SIGNAL("triggered()"), self.aliasdock.alias.model.addAlias)
        ## Tree connection
        QtCore.QObject.connect(self.tree, QtCore.SIGNAL("doubleClicked (const QModelIndex&)"), self.GetIdByTree)
        ## Tree item informations
        QtCore.QObject.connect(self.tree, QtCore.SIGNAL("clicked (const QModelIndex&)"), self.showInformations)

        # "Connect" menus
        self.menubar.enableItems()

        # "Connect" groups
        self.groups.connection()

    def exec_(self):
        """
            Show default and load dock positions if necessary
        """
        if self.settings.value("SFLvault-qt4/savewindow").toInt()[0] == QtCore.Qt.Checked:
            if self.settings.value("SFLvault-qt4/binsavewindow").toByteArray():
                t = self.restoreState(self.settings.value("SFLvault-qt4/binsavewindow").toByteArray())
        if self.settings.value("SFLvault-qt4/autoconnect").toInt()[0] == QtCore.Qt.Checked:
            self.vaultConnection()
        self.loadUnloadSystrayConfig()
        self.disEnableEffectsConfig()
        self.showHideFilterBarConfig()
        self.show()

    def loadUnloadSystrayConfig(self):
        """
            Load or unload systray
        """
        if self.settings.value("SFLvault-qt4/systray").toInt()[0] == QtCore.Qt.Checked:
            self.systray.show()
        elif self.settings.value("SFLvault-qt4/systray").toInt()[0] == QtCore.Qt.Unchecked:
            self.systray.hide()


    def disEnableEffectsConfig(self):
        """
            Enable or not effects
        """
        if self.settings.value("SFLvault-qt4/effects").toInt()[0] == QtCore.Qt.Checked:
            self.setAnimated(True)
            self.tree.setAnimated(True)
        elif self.settings.value("SFLvault-qt4/effects").toInt()[0] == QtCore.Qt.Unchecked:
            self.setAnimated(False)
            self.tree.setAnimated(False)

    def showHideFilterBarConfig(self):
        if self.settings.value("SFLvault-qt4/filter").toInt()[0] == QtCore.Qt.Checked:
            self.treewidget.filter.show()
        elif self.settings.value("SFLvault-qt4/effects").toInt()[0] == QtCore.Qt.Unchecked:
            self.treewidget.filter.hide()
 
    def setShortcut(self):
        """
            Set shortcuts
        """
        QtGui.QShortcut(QtGui.QKeySequence(QtCore.Qt.CTRL + QtCore.Qt.Key_I),
                        self, self.showHideFilterShort )
        QtGui.QShortcut(QtGui.QKeySequence(QtCore.Qt.CTRL + QtCore.Qt.Key_F),
                        self, self.searchShort )

    def searchShort(self):
        """
            Show search dock and set focus
        """
        if not self.searchdock.isVisible():
            self.searchdock.show()
        self.searchdock.search.search.setFocus()

    def showHideFilterShort(self):
        """
            Hide or show filter bar
        """
        if self.treewidget.filter.isVisible():
            self.treewidget.filter.hide()
        else:
            self.treewidget.filter.show()
            self.treewidget.filter.filter_input.setFocus()

    def quickConnection(self):
        """
            Launch connection from shortcut
        """
        ret, ok = QtGui.QInputDialog.getText(self.parent, self.tr("Quick connection"),
                                                 self.tr("Service id or service alias :"),
                                                 QtGui.QLineEdit.Normal)
        if not ok or not ret:
            return False

        # Try to know if id is a integer
        id, bool = ret.toInt()
        if not bool:
            # if is not a integer, then it's a QString
            # check if it's something like s#111
            ret = unicode(ret)
            if ret.startswith("s#"):
                id = ret.split("#")[1]
            if not id:
            # Then it's an alias
                id = getAlias(ret)
                if id:
                    id = id.split("#")[1]
        # Finally launch connection
        if id:
            self.connection(id)
        else:
            ErrorMessage("No service found")
        
