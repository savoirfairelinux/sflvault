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
        global token

    def setHeaders(self):
        self.setColumnCount(2)
        self.setRowCount(0)
        self.setHeaderData(0, QtCore.Qt.Horizontal, QtCore.QVariant("Id"))
        self.setHeaderData(1, QtCore.Qt.Horizontal, QtCore.QVariant("Url"))

    def readConfig(self):
        for alias, id in token.alias_list():
            self.addFavorite(id, alias)

    def saveFavorite(self, id=None, alias=None):
        token.alias_add(alias,id)
#        self.settings.setValue("favorites/" + id, QtCore.QVariant(url))
        # Save config
#        self.settings.saveConfig()
    
    def addFavorite(self, id=None, alias=None):
        # Added by context menu
        if not id and not alias:
            alias, ok = QtGui.QInputDialog.getText(self.parent, self.tr("New Alias"),
                                                    self.tr("Alias name:"),
                                                    QtGui.QLineEdit.Normal)
            id_index = self.tree.selectedIndexes()[1]
            id  = self.tree.model().data(id_index).toString()
            id = "s#" + id

        self.insertRow(0)
        self.setData(self.index(0, 1), QtCore.QVariant(alias))
        self.setData(self.index(0, 0), QtCore.QVariant(id))
        self.saveFavorite(unicode(id), unicode(alias))

    def delFavorite(self):
        """
            Delete selected row
        """
        
        selected_row = self.parent.favorite_list.selectedIndexes()[1]
        alias = unicode(self.data(selected_row).toString())
        token.alias_del(alias)
 

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
