#!/usr/bin/env python
# -*- coding: UTF-8 -*-

import sys
from PyQt4 import QtCore, QtGui
import re
from PyQt4.QtCore import Qt
import sflvault
from tree.tree import TreeVault, TreeView
from docks.servicedock import ServiceInfoDock
from docks.infodock import InfoDock
from docks.machinedock import MachineInfoDock
from docks.customerdock import CustomerInfoDock
from docks.searchdock import SearchDock
from docks.favoritedock import FavoriteDock
from config.protocols import ProtocolsWidget
from config.groups import GroupsWidget
from config.config import Config
from bar.menubar import MenuBar
from sflvault.client import SFLvaultClient
import shutil
import os



from auth import auth
token = auth.getAuth()



class MainWindow(QtGui.QMainWindow):
    def __init__(self, parent=None):
        QtGui.QMainWindow.__init__(self, parent)
        self.parent = parent

        # Load settings
        self.settings = Config(parent=self)

        # Load GUI item
        self.treewidget = TreeVault(parent=self)
        self.tree = self.treewidget.tree
        self.serviceinfodock = ServiceInfoDock(parent=self)
        self.machineinfodock = MachineInfoDock(parent=self)
        self.customerinfodock = CustomerInfoDock(parent=self)
        self.searchdock = SearchDock(parent=self)
        self.infodock = InfoDock(parent=self)
        self.favoritedock = FavoriteDock(parent=self)
        self.menubar = MenuBar(parent=self)

        # Create clipboard
        self.clipboard = QtGui.QApplication.clipboard()

        # Get favorite list
        self.favorite_list = self.favoritedock.favorite.favorite_list

        # Attach items to mainwindow
        self.setCentralWidget(self.treewidget)
        self.addDockWidget(QtCore.Qt.RightDockWidgetArea,self.customerinfodock)
        self.addDockWidget(QtCore.Qt.RightDockWidgetArea,self.machineinfodock)
        self.addDockWidget(QtCore.Qt.RightDockWidgetArea,self.serviceinfodock)
        self.addDockWidget(QtCore.Qt.RightDockWidgetArea,self.infodock)
        self.addDockWidget(QtCore.Qt.TopDockWidgetArea,self.searchdock)
        self.addDockWidget(QtCore.Qt.LeftDockWidgetArea,self.favoritedock)
        self.setMenuBar(self.menubar)

        # Load windows
        self.protocols = ProtocolsWidget(parent=self)
        self.groups = GroupsWidget(parent=self)

        # Signals
        ## Tree connection
        QtCore.QObject.connect(self.tree, QtCore.SIGNAL("doubleClicked (const QModelIndex&)"), self.GetIdByTree)
        ## Tree item informations
        QtCore.QObject.connect(self.tree, QtCore.SIGNAL("clicked (const QModelIndex&)"), self.showInformations)
        ## Tree Search
        QtCore.QObject.connect(self.searchdock.search.search, QtCore.SIGNAL("textEdited (const QString&)"), self.search)
        ## Tree filter by groups
        QtCore.QObject.connect(self.searchdock.search.groups, QtCore.SIGNAL("currentIndexChanged (const QString&)"), self.search)
        ## Protocols
        QtCore.QObject.connect(self.menubar.protocols, QtCore.SIGNAL("triggered()"), self.protocols.exec_)
        ## Groups
        QtCore.QObject.connect(self.menubar.groups, QtCore.SIGNAL("triggered()"), self.groups.exec_)
        ## Alias
        QtCore.QObject.connect(self.tree.bookmarkAct, QtCore.SIGNAL("triggered()"), self.favoritedock.favorite.model.addFavorite)
        ## Alias connection
        QtCore.QObject.connect(self.favoritedock.favorite.favorite_list, QtCore.SIGNAL("doubleClicked (const QModelIndex&)"), self.GetIdByBookmark)

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
                self.serviceinfodock.showInformations(idserv)
            else:
                # Selected item is a machine
                # Get machine parent id (customerid)
                parentIndex = self.tree.proxyModel.parent(index)
                parentIndex1 = self.tree.proxyModel.index(parentIndex.row(), 1, parentIndex.parent())
                idcust,bool = self.tree.proxyModel.data(parentIndex1, QtCore.Qt.DisplayRole).toInt()
                # Get machine id 
                idmach,bool = indexId.data(QtCore.Qt.DisplayRole).toInt()
                self.serviceinfodock.showInformations(None)
            self.machineinfodock.showInformations(idmach)
        else:
            # Selected item is a customer
            idcust,bool = indexId.data(QtCore.Qt.DisplayRole).toInt()
            self.machineinfodock.showInformations(None)
            self.serviceinfodock.showInformations(None)
        self.customerinfodock.showInformations(idcust)

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
        global token
        # Get Options
        options = {}
        service = token.vault.service_get(token.authtok, idserv)
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
        global token
        self.clipboard.setText(token.service_get(serviceid)["plaintext"])
