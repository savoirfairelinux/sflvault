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


class ProtocolsWidget(QtGui.QDialog):
    def __init__(self, parent=None):
        QtGui.QDialog.__init__(self, parent)
        self.parent = parent
        self.settings = self.parent.settings
        self.model = ProtocolModel(self)
        self.protocols = {}

        # Load gui items
        self.addprotocol = QtGui.QPushButton(self.tr("Add"))
        self.removeprotocol = QtGui.QPushButton(self.tr("Remove"))
        okButton = QtGui.QPushButton(self.tr("OK"))
        cancelButton = QtGui.QPushButton(self.tr("Cancel"))
        groupbox = QtGui.QGroupBox()
        # Configure table view
        self.protocol_list = QtGui.QTableView(self)
        self.protocol_list.setModel(self.model)
        self.protocol_list.setSelectionBehavior(QtGui.QAbstractItemView.SelectRows)
        self.protocol_list.setSortingEnabled(1)
        self.protocol_list.setSelectionMode(QtGui.QAbstractItemView.SingleSelection)
        self.protocol_list.adjustSize()
        ### MARCHE PAS
#        h = self.protocol_list.horizontalHeader()
#        h.setResizeMode(0, QtGui.QHeaderView.Fixed)
#        h.setResizeMode(1, QtGui.QHeaderView.Interactive)
#        h.setResizeMode(2, QtGui.QHeaderView.Stretch)
#        h.resizeSection(0,50)
#        h.resizeSection(1,2000)

        # Positionning items
        gridLayout = QtGui.QGridLayout()
        gridLayout.addWidget(self.protocol_list,0,1,3,1)
        gridLayout.addWidget(self.addprotocol,0,0)
        gridLayout.addWidget(self.removeprotocol,2,0)
        groupbox.setLayout(gridLayout)

        buttonLayout = QtGui.QHBoxLayout()
        buttonLayout.addStretch(1)
        buttonLayout.addWidget(okButton)
        buttonLayout.addWidget(cancelButton)

        mainLayout = QtGui.QVBoxLayout()
        mainLayout.addWidget(groupbox)
        mainLayout.addLayout(buttonLayout)
        self.setLayout(mainLayout)

        self.setWindowTitle(self.tr("Procotols management"))

        # SIGNALS
        QtCore.QObject.connect(self.addprotocol, QtCore.SIGNAL("clicked()"), self.model.addProtocol)
        QtCore.QObject.connect(self.removeprotocol, QtCore.SIGNAL("clicked()"), self.model.delProtocol)
        QtCore.QObject.connect(okButton, QtCore.SIGNAL("clicked()"), self.saveConfig)
        QtCore.QObject.connect(cancelButton, QtCore.SIGNAL("clicked()"), self, QtCore.SLOT("reject()"))

    def exec_(self):
        # load config
        self.readConfig()
        # Show dialog
        self.show()

    def delRow(self):
        """
            Delete selected row
        """
        # Delete current row
        selected_rows = self.protocol_list.selectedIndexes()
        for selected_row in selected_rows:
            self.model.removeRows(selected_row.row(), 1)

    def readConfig(self):
        """
            ReadConfig and add in model
        """
        # Clear model
        self.model.clear()
        # Create headers
        self.model.setHeaders()
        for protocol in self.settings.readConfig("protocols"):
            # Create new items
            command = self.settings.value("protocols/" + protocol).toString()
            self.model.addProtocol(protocol, command)
            self.protocol_list.resizeColumnsToContents()
            # Save protocol in protocol list
            self.protocols[str(protocol)] = str(self.settings.value("protocols/" + protocol).toString())

    def saveConfig(self):
        # Clear Config
        for protocol in self.protocols.keys():
            self.settings.remove("protocols/" + protocol)
        # Write new config
        for row in range(self.model.rowCount()) :
            protocol = self.model.data(self.model.index(row,0)).toString()
            command = self.model.data(self.model.index(row,1)).toString()
            self.settings.setValue("protocols/" + protocol, QtCore.QVariant(command))
        # Save config
        self.settings.saveConfig()
        # Close dialog
        self.accept()


class ProtocolModel(QtGui.QStandardItemModel):
    def __init__(self, parent=None):
        QtGui.QStandardItemModel.__init__(self, 0, 3, parent)
        self.parent = parent

    def setHeaders(self):
        self.setColumnCount(3)
        self.setRowCount(0)
        self.setHeaderData(0, QtCore.Qt.Horizontal, QtCore.QVariant("Protocol"))
        self.setHeaderData(1, QtCore.Qt.Horizontal, QtCore.QVariant("Command"))
        self.setHeaderData(2, QtCore.Qt.Horizontal, QtCore.QVariant("Copy password to clipboard"))

    def addProtocol(self, protocol=None, command=None):
        self.insertRow(0)
        self.setData(self.index(0, 0), QtCore.QVariant(protocol))
        self.setData(self.index(0, 1), QtCore.QVariant(command))

    def delProtocol(self):
        """
            Delete selected row
        """
        # Delete current row
        selected_row = self.parent.protocol_list.selectedIndexes()[0]
        self.removeRows(selected_row.row(), 1)

