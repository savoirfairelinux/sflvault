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
from lib.auth import *


class AliasDock(QtGui.QDockWidget):
    def __init__(self, parent=None):
        QtGui.QDockWidget.__init__(self, "Aliases", parent)
        self.parent = parent
        self.alias = Alias(self)
        self.setWidget(self.alias)
        self.setShortcut()

        ## Check visibility
        QtCore.QObject.connect(self, QtCore.SIGNAL("visibilityChanged (bool)"), self.parent.menubar.checkDockBoxes)

    def readAliases(self):
        self.alias.model.clear()
        self.alias.model.setHeaders()
        self.alias.model.readConfig()
        self.setGeometries()

    def setGeometries(self):
        """
            Set headers size
        """
        h = self.alias.alias_list.header()
        h.setResizeMode(0, QtGui.QHeaderView.Stretch)
        h.setStretchLastSection(0)
        self.alias.alias_list.setColumnWidth(1,65)

    def setShortcut(self):
        """
            Define tree shortcuts
        """
        QtGui.QShortcut(QtGui.QKeySequence(QtCore.Qt.Key_Delete),
                self.alias.alias_list, self.alias.model.delAlias)
        QtGui.QShortcut(QtGui.QKeySequence(QtCore.Qt.Key_F2),
                self.alias.alias_list, self.alias.model.editAlias)


class Alias(QtGui.QWidget):
    def __init__(self, parent=None, ):
        QtGui.QWidget.__init__(self, parent)
        self.parent = parent

        # Load model
        self.model = AliasModel(self)

        # Load gui items
        self.alias_list = AliasView(self)

        # Attach model
        self.alias_list.setModel(self.model)

        # QGridLayout
        mainLayout = QtGui.QGridLayout()
        mainLayout.addWidget(self.alias_list,0,0)

        # Geometries
        self.setWindowTitle(self.tr("Alias"))

        # Show window
        self.setLayout(mainLayout)


class AliasModel(QtGui.QStandardItemModel):
    def __init__(self, parent=None):
        QtGui.QStandardItemModel.__init__(self, 0, 2, parent)
        self.parent = parent
        self.setHeaders()
        self.tree = self.parent.parent.parent.tree
        self.settings = self.parent.parent.parent.settings

    def setHeaders(self):
        """
            Set Headers
        """
        self.setColumnCount(2)
        self.setRowCount(0)
        self.setHeaderData(0, QtCore.Qt.Horizontal, QtCore.QVariant("Name"))
        self.setHeaderData(1, QtCore.Qt.Horizontal, QtCore.QVariant("Id"))
       
    def readConfig(self):
        """
            Read config to get aliases
        """
        for alias, id in getAliasList():
            self.addAlias(id, alias)

    def savAlias(self, id=None, alias=None):
        """
            Save alias in config
        """
        saveAlias(alias,id)
    
    def addAlias(self, id=None, alias=None, rowNumber=0):
        """
            Added by context menu
        """
        if not id and not alias:
            alias, ok = QtGui.QInputDialog.getText(self.parent, self.tr("Edit alias"),
                                                    self.tr("New alias name:"),
                                                    QtGui.QLineEdit.Normal)
            if not ok or not alias:
                return False
            id_index = self.tree.selectedIndexes()[1]
            id  = self.tree.model().data(id_index).toString()

        self.insertRow(rowNumber)
        self.setData(self.index(rowNumber, 0), QtCore.QVariant(alias))
        self.setData(self.index(rowNumber, 1), QtCore.QVariant(id))
        self.savAlias(unicode(id), unicode(alias))

    def delAlias(self,selected_row=None):
        """
            Delete selected row
            and alias in config
        """
        if not selected_row:
            selected_row = self.parent.alias_list.selectedIndexes()
        alias = unicode(self.data(selected_row[0]).toString())
        self.removeRows(selected_row[0].row(), 1)
        # This function comes from the sflvault api
        delAlias(alias)
 
    def editAlias(self, id=None, alias=None):
        """
            Edit alias from context menu
        """
        if not id and not alias:
            selected_row = self.parent.alias_list.selectedIndexes()
            alias = unicode(self.data(selected_row[0]).toString())
            id = unicode(self.data(selected_row[1]).toString())
            alias, ok = QtGui.QInputDialog.getText(self.parent, self.tr("Edit Alias"),
                                                    self.tr("new name:"),
                                                    QtGui.QLineEdit.Normal, alias)
            if not ok or not alias:
                return False

        rowNumber = selected_row[0].row()
        self.delAlias(selected_row)
        self.addAlias(unicode(id),unicode(alias),rowNumber)
 

class AliasView(QtGui.QTreeView):
    def __init__(self, parent=None):
        QtGui.QTreeView.__init__(self, parent)
        self.parentView = parent

        # Set behavior
        self.setSelectionBehavior(QtGui.QAbstractItemView.SelectRows)
        self.setSortingEnabled(1)
        self.setSelectionMode(QtGui.QAbstractItemView.SingleSelection)
        self.setEditTriggers(QtGui.QAbstractItemView.NoEditTriggers)
        self.setRootIsDecorated(False)
        self.setAlternatingRowColors(True)
        # Create menu
        self.createActions()

    def contextMenuEvent(self, event):
        """
            Create contextMenu on right click
        """
        menu = QtGui.QMenu(self)
        menu.addAction(self.delAct)
        menu.addAction(self.editAct)
        menu.exec_(event.globalPos())

    def createActions(self):
        """
            Create actions for contextMenu
        """
        self.delAct = QtGui.QAction(self.tr("&Delete bookmark..."), self)
        self.delAct.setStatusTip(self.tr("Delete bookmark"))
        self.connect(self.delAct, QtCore.SIGNAL("triggered()"), self.parentView.model.delAlias)
        self.editAct = QtGui.QAction(self.tr("&Edit bookmark..."), self)
        self.editAct.setStatusTip(self.tr("Edit bookmark"))
        self.connect(self.editAct, QtCore.SIGNAL("triggered()"), self.parentView.model.editAlias)
