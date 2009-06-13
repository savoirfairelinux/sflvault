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
from docks.favoritedock import FavoriteDock
from config.protocols import ProtocolsWidget
from config.groups import GroupsWidget
from config.config import Config
from bar.menubar import MenuBar
from sflvault.client import SFLvaultClient
import shutil
import os

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
        self.favoritedock = FavoriteDock(parent=self)
        self.searchdock = SearchDock(parent=self)
        self.infodock = InfoDock(parent=self)
        self.menubar = MenuBar(parent=self)

        # Create clipboard
        self.clipboard = QtGui.QApplication.clipboard()

        # Load favorite list
        self.favorite_list = self.favoritedock.favorite.favorite_list

        # Attach items to mainwindow
        self.setCentralWidget(self.treewidget)
        self.addDockWidget(QtCore.Qt.LeftDockWidgetArea,self.favoritedock)
        self.addDockWidget(QtCore.Qt.RightDockWidgetArea,self.infodock)
        self.addDockWidget(QtCore.Qt.TopDockWidgetArea,self.searchdock)
        self.setMenuBar(self.menubar)

        # Read aliases
        self.favoritedock.readAliases()

        # Load windows
        self.protocols = ProtocolsWidget(parent=self)
        self.groups = GroupsWidget(parent=self)

        # Signals
        ## Protocols
        QtCore.QObject.connect(self.menubar.protocols, QtCore.SIGNAL("triggered()"), self.protocols.exec_)
        ## Groups
        QtCore.QObject.connect(self.menubar.groups, QtCore.SIGNAL("triggered()"), self.groups.exec_)
        ## Vault connection
        QtCore.QObject.connect(self.menubar.connection, QtCore.SIGNAL("triggered()"), self.vaultConnection)

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
                idmach,bool = self.tree.proxyModel.data(parentIndex1, QtCore.Qt.DisplayRole).toInt()
                # Get machine parent id (customerid)
                parentIndex = self.tree.proxyModel.parent(parentIndex)
                parentIndex1 = self.tree.proxyModel.index(parentIndex.row(), 1, parentIndex.parent())
                idcust,bool = self.tree.proxyModel.data(parentIndex1, QtCore.Qt.DisplayRole).toInt()
                # Get service id 
                idserv,bool = indexId.data(QtCore.Qt.DisplayRole).toInt()
            else:
                # Selected item is a machine
                # Get machine parent id (customerid)
                parentIndex = self.tree.proxyModel.parent(index)
                parentIndex1 = self.tree.proxyModel.index(parentIndex.row(), 1, parentIndex.parent())
                idcust,bool = self.tree.proxyModel.data(parentIndex1, QtCore.Qt.DisplayRole).toInt()
                # Get machine id 
                idmach,bool = indexId.data(QtCore.Qt.DisplayRole).toInt()
                idserv = None
        else:
            # Selected item is a customer
            idcust,bool = indexId.data(QtCore.Qt.DisplayRole).toInt()
            idmach = None
            idserv = None
        self.infodock.showInformations(idcust, machineid=idmach, serviceid=idserv)

    def GetIdByTree(self, index):
        """
            Get selected item id in tree and launch connection
        """
        # Get Id colunm
        indexId = self.tree.selectedIndexes()[1]
        idserv,bool = indexId.data(QtCore.Qt.DisplayRole).toInt()
        # Check if seleted item is a service
        if index.parent().parent().isValid():
            self.connection(idserv)

    def GetIdByBookmark(self, index):
        """
            Get selected item id in bookmark and launch connection
        """
        # Get Id colunm
        indexId = self.favorite_list.selectedIndexes()[0]
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
        url = service["service"]["url"]
        protocol, address = url.split("://")
        options["user"], options["address"] = address.split("@", 1)
        options["id"] = service["service"]["id"]
        options["vaultconnect"] = "sflvault connect %s" % options["id"]
        # Copy password to clipboard
        self.passtoclip(idserv)
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

        ## "Connect" Alias
        QtCore.QObject.connect(self.favoritedock.favorite.favorite_list, QtCore.SIGNAL("doubleClicked (const QModelIndex&)"), self.GetIdByBookmark) 

        # "Connect" search dock
        # Update Group list in search box
        self.searchdock.connection()

        # "Connect" tree
        ## Tree Search
        QtCore.QObject.connect(self.searchdock.search.search, QtCore.SIGNAL("textEdited (const QString&)"), self.search)
        ## Tree filter by groups
        QtCore.QObject.connect(self.searchdock.search.groups, QtCore.SIGNAL("currentIndexChanged (const QString&)"), self.search)
        self.tree.search(None, None)
        ## Tree bookmark
        QtCore.QObject.connect(self.tree.bookmarkAct, QtCore.SIGNAL("triggered()"), self.favoritedock.favorite.model.addFavorite)
        ## Tree connection
        QtCore.QObject.connect(self.tree, QtCore.SIGNAL("doubleClicked (const QModelIndex&)"), self.GetIdByTree)
        ## Tree item informations
        QtCore.QObject.connect(self.tree, QtCore.SIGNAL("clicked (const QModelIndex&)"), self.showInformations)

        # "Connect" menus
        self.menubar.enableItems()

        # "Connect" groups
        self.groups.connection()
