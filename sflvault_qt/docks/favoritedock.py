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


from auth import auth
token = auth.getAuth()

class FavoriteDock(QtGui.QDockWidget):
    def __init__(self, parent=None, ):
        QtGui.QDockWidget.__init__(self, "Favorites", parent)
        self.parent = parent
        self.favorite = Favorite(self)
        self.setWidget(self.favorite)

class Favorite(QtGui.QWidget):
    def __init__(self, parent=None, ):
        QtGui.QWidget.__init__(self, parent)
        self.parent = parent

        # Load model
        self.model = FavoriteModel(self)

        # Load gui items
#        self.favorite_list = QtGui.QTableView(self)
        self.favorite_list = FavoriteView(self)

        # Attach model
        self.favorite_list.setModel(self.model)

        # QGridLayout
        mainLayout = QtGui.QGridLayout()
        mainLayout.addWidget(self.favorite_list,0,0)

        # Geometries
        self.setWindowTitle(self.tr("Favorites"))

        # Show window
        self.setLayout(mainLayout)


class FavoriteModel(QtGui.QStandardItemModel):
    def __init__(self, parent=None):
        QtGui.QStandardItemModel.__init__(self, 0, 2, parent)
        self.parent = parent
        self.setHeaders()
        self.tree = self.parent.parent.parent.tree
        self.settings = self.parent.parent.parent.settings
        self.readConfig()

    def setHeaders(self):
        self.setColumnCount(2)
        self.setRowCount(0)
        self.setHeaderData(0, QtCore.Qt.Horizontal, QtCore.QVariant("Id"))
        self.setHeaderData(1, QtCore.Qt.Horizontal, QtCore.QVariant("Url"))

    def readConfig(self):
        for favorite_id in self.settings.readConfig("favorites"):
            url = self.settings.value("favorites/" + favorite_id).toString()
            self.addFavorite(favorite_id, url)

    def saveFavorite(self, id=None, url=None):
        self.settings.setValue("favorites/" + id, QtCore.QVariant(url))
        # Save config
        self.settings.saveConfig()
    
    def addFavorite(self, id=None, url=None):
        # Added by context menu
        if not id and not url:
            id_index = self.tree.selectedIndexes()[1]
            id  = self.tree.model().data(id_index).toString()
            url_index = self.tree.selectedIndexes()[0]
            url = self.tree.model().data(url_index).toString()

        self.insertRow(0)
        self.setData(self.index(0, 1), QtCore.QVariant(url))
        self.setData(self.index(0, 0), QtCore.QVariant(id))
        self.saveFavorite(id, url)

    def delFavorite(self):
        """
            Delete selected row
        """
        # Delete current row
        selected_row = self.parent.favorite_list.selectedIndexes()[0]
        id = self.data(selected_row).toString()
        self.removeRows(selected_row.row(), 1)
        self.settings.remove("favorites/" + id)
        # Save config
        self.settings.saveConfig()
 

class FavoriteView(QtGui.QTreeView):
    def __init__(self, parent=None):
        QtGui.QTreeView.__init__(self, parent)
        self.parentView = parent

        self.setSelectionBehavior(QtGui.QAbstractItemView.SelectRows)
        self.setSortingEnabled(1)
        self.setSelectionMode(QtGui.QAbstractItemView.SingleSelection)
        self.setEditTriggers(QtGui.QAbstractItemView.NoEditTriggers)
        self.setRootIsDecorated(False)
        self.createActions()

    def contextMenuEvent(self, event):
        """
            Create contextMenu on right click
        """
        menu = QtGui.QMenu(self)
        menu.addAction(self.delAct)
        menu.exec_(event.globalPos())

    def createActions(self):
        """
            Create actions for contextMenu
        """
        self.delAct = QtGui.QAction(self.tr("&Delete bookmark..."), self)
        #self.delAct.setShortcut(self.tr("Ctrl+X"))
        self.delAct.setStatusTip(self.tr("Delete bookmark"))
        self.connect(self.delAct, QtCore.SIGNAL("triggered()"), self.parentView.model.delFavorite)


