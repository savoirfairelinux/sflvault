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
        label = QtGui.QLabel("Here you can choose which command will be\
                                launch when you want to connect to a service.<br/>\
                                You can use several parameters from the service :\
                                <ul>\
                                <li> %(user)s          :</li>\
                                <li> %(address)s       :</li>\
                                <li> %(vaultid)s       :</li>\
                                <li> %(vaultconnect)s  :</li>\
                                </ul>\
                                Exemples :\
                                <dl>\
                                <dd><i>konsole -e %(vaultconnect)s</i></dd>\
                                <dt>launch : konsole -e sflvault connect s#133</dt>\
                                <dd><i>firefox %(address)s</i></dd>\
                                <dt>launch : firefox http://website.org</dt>\
                                <dt>(which open firefox with the wanted page)</dt>\
                                </dl>\
                                ")
        label.setAlignment(QtCore.Qt.AlignLeft)        
        label.setTextFormat(QtCore.Qt.RichText)
        label.setTextInteractionFlags(QtCore.Qt.TextBrowserInteraction)
                        
        self.addprotocol = QtGui.QPushButton(self.tr("Add"))
        self.removeprotocol = QtGui.QPushButton(self.tr("Remove"))
        save = QtGui.QPushButton(self.tr("Save"))
        reload = QtGui.QPushButton(self.tr("Reload"))
        cancel = QtGui.QPushButton(self.tr("Cancel"))
        groupbox = QtGui.QGroupBox()
        # Configure table view
        self.protocol_list = QtGui.QTableView(self)
        self.protocol_list.setModel(self.model)
        self.protocol_list.setSelectionBehavior(QtGui.QAbstractItemView.SelectRows)
        self.protocol_list.setSortingEnabled(1)
        self.protocol_list.setSelectionMode(QtGui.QAbstractItemView.SingleSelection)
        self.protocol_list.adjustSize()


        # Positionning items
        gridLayout = QtGui.QGridLayout()
        gridLayout.addWidget(self.protocol_list,0,0,1,6)
        gridLayout.addWidget(self.addprotocol,1,1)
        gridLayout.addWidget(self.removeprotocol,1,4)
        gridLayout.addWidget(label,2,0,1,6)
        groupbox.setLayout(gridLayout)

        buttonLayout = QtGui.QHBoxLayout()
        buttonLayout.addStretch(1)
        buttonLayout.addWidget(reload)
        buttonLayout.addWidget(save)
        buttonLayout.addWidget(cancel)

        mainLayout = QtGui.QVBoxLayout()
        mainLayout.addWidget(groupbox)
        mainLayout.addLayout(buttonLayout)
        self.setLayout(mainLayout)

        self.setWindowTitle(self.tr("Procotols management"))

        # SIGNALS
        QtCore.QObject.connect(self.addprotocol, QtCore.SIGNAL("clicked()"), self.model.addProtocol)
        QtCore.QObject.connect(self.removeprotocol, QtCore.SIGNAL("clicked()"), self.model.delProtocol)
        QtCore.QObject.connect(save, QtCore.SIGNAL("clicked()"), self.saveConfig)
        QtCore.QObject.connect(reload, QtCore.SIGNAL("clicked()"), self.readConfig)
        QtCore.QObject.connect(cancel, QtCore.SIGNAL("clicked()"), self, QtCore.SLOT("reject()"))

    def exec_(self):
        # load config
        self.readConfig()
        # Show dialog
        self.show()
        self.resize(600,500)

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
        # Set Geometries
        self.setGeometries()

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

    def setGeometries(self):
        h = self.protocol_list.horizontalHeader()
        h.setResizeMode(0, QtGui.QHeaderView.Fixed)
        h.setResizeMode(1, QtGui.QHeaderView.Stretch)
        h.setStretchLastSection(0)
        self.protocol_list.setColumnWidth(0,100)
        self.protocol_list.setColumnWidth(2,100)
        h = self.protocol_list.verticalHeader()
        h.hide()



class ProtocolModel(QtGui.QStandardItemModel):
    def __init__(self, parent=None):
        QtGui.QStandardItemModel.__init__(self, 0, 3, parent)
        self.parent = parent

    def setHeaders(self):
        self.setColumnCount(3)
        self.setRowCount(0)
        self.setHeaderData(0, QtCore.Qt.Horizontal, QtCore.QVariant("Protocol"))
        self.setHeaderData(1, QtCore.Qt.Horizontal, QtCore.QVariant("Command"))
        self.setHeaderData(2, QtCore.Qt.Horizontal, QtCore.QVariant("Pass to Clip"))

    def addProtocol(self, protocol=None, command=None):
        self.insertRow(0)
        self.setData(self.index(0, 0), QtCore.QVariant(protocol))
        self.setData(self.index(0, 1), QtCore.QVariant(command))

    def delProtocol(self):
        """
            Delete selected row
        """
        # Delete current row
        if self.parent.protocol_list.selectedIndexes():
            selected_row = self.parent.protocol_list.selectedIndexes()[0]
            self.removeRows(selected_row.row(), 1)

