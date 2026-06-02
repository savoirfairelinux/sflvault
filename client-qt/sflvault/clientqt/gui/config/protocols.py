#!/usr/bin/env python
# -*- coding: UTF-8 -*-
#
#    sflvault_qt/config/protocols.py
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
from PyQt5 import QtCore, QtGui, QtWidgets
import re
from PyQt5.QtCore import Qt
import sflvault
from sflvault.client import SFLvaultClient
import shutil
import os


class ProtocolsWidget(QtWidgets.QDialog):
    def __init__(self, parent=None):
        QtWidgets.QDialog.__init__(self, parent)
        self.parent = parent
        self.settings = self.parent.settings
        self.model = ProtocolModel(self)

        # Load gui items
        label = QtWidgets.QLabel("Here you can choose which command will be\
                                launch when you want to connect to a service.<br/>\
                                You can use several parameters from the service :\
                                <table>\
                                <tr><td> - %(user)s         : </td><td> User name of the service </td></tr>\
                                <tr><td> - %(address)s      : </td><td> Address of the service (without protocol)</td></tr>\
                                <tr><td> - %(protocol)s     : </td><td> Protocol of the service</td></tr>\
                                <tr><td> - %(password)s     : </td><td> Password of the service</td></tr>\
                                <tr><td> - %(vaultid)s      : </td><td> Vault id of the service </td></tr>\
                                <tr><td> - %(vaultconnect)s : </td><td> Vault connection command </td></tr>\
                                </table>\
                                Exemples :\
                                <dl>\
                                <dd><i>konsole -e %(vaultconnect)s</i></dd>\
                                <dt>launch : konsole -e sflvault connect s#133</dt>\
                                <dd><i>firefox %(address)s</i></dd>\
                                <dt>launch : firefox website.org</dt>\
                                <dt>(which open firefox with the wanted page)</dt>\
                                </dl>\
                                ")
        label.setAlignment(QtCore.Qt.AlignLeft)        
        label.setTextFormat(QtCore.Qt.RichText)
        label.setTextInteractionFlags(QtCore.Qt.TextBrowserInteraction)
                        
        self.addprotocol = QtWidgets.QPushButton(self.tr("Add"))
        self.removeprotocol = QtWidgets.QPushButton(self.tr("Remove"))
        save = QtWidgets.QPushButton(self.tr("Save"))
        reload = QtWidgets.QPushButton(self.tr("Reload"))
        cancel = QtWidgets.QPushButton(self.tr("Cancel"))
        groupbox = QtWidgets.QGroupBox()
        # Configure table view
        self.protocol_list = ProtocolView(self)
        self.protocol_list.setModel(self.model)
        self.protocol_list.setSelectionBehavior(QtWidgets.QAbstractItemView.SelectRows)
        self.protocol_list.setSortingEnabled(1)
        self.protocol_list.setSelectionMode(QtWidgets.QAbstractItemView.SingleSelection)
        self.protocol_list.adjustSize()


        # Positionning items
        gridLayout = QtWidgets.QGridLayout()
        gridLayout.addWidget(self.protocol_list,0,0,1,6)
        gridLayout.addWidget(self.addprotocol,1,1)
        gridLayout.addWidget(self.removeprotocol,1,4)
        gridLayout.addWidget(label,2,0,1,6)
        groupbox.setLayout(gridLayout)

        buttonLayout = QtWidgets.QHBoxLayout()
        buttonLayout.addStretch(1)
        buttonLayout.addWidget(cancel)
        buttonLayout.addWidget(reload)
        buttonLayout.addWidget(save)

        mainLayout = QtWidgets.QVBoxLayout()
        mainLayout.addWidget(groupbox)
        mainLayout.addLayout(buttonLayout)
        self.setLayout(mainLayout)

        self.setWindowTitle(self.tr("Procotols management"))

        # SIGNALS
        self.addprotocol.clicked.connect(self.model.addProtocol)
        self.removeprotocol.clicked.connect(self.model.delProtocol)
        save.clicked.connect(self.saveConfig)
        reload.clicked.connect(self.readConfig)
        cancel.clicked.connect(self.reject)
        
        # FIXME set return shortcut to save config only
        # when editor mode in table view is not enabled
        QtWidgets.QShortcut(QtGui.QKeySequence(QtCore.Qt.Key_Return), self)

    def exec_(self):
        """
            Open window
        """
        # load config
        self.readConfig()
        # Show dialog
        self.show()
        self.resize(1000,700)

    def readConfig(self):
        """
            ReadConfig and add in model
        """
        # Clear model
        self.model.clear()
        self.model.protocols = []
        # Create headers
        self.model.setHeaders()
        for protocol_name in self.settings.readConfig("protocols"):
            # Get values in config
            protocol_name = str(protocol_name)
            command = self.settings.value("protocols/" + protocol_name + "/command", "")
            args = self.settings.value("protocols/" + protocol_name + "/args", "")
            clip = int(self.settings.value("protocols/" + protocol_name + "/clip", 0))
            tooltip = int(self.settings.value("protocols/" + protocol_name + "/tooltip", 0))
            # Create new item
            self.model.addProtocol(protocol_name, command, args, clip, tooltip)
        # Set Geometries
        self.setGeometries()

    def saveConfig(self):
        """
            Save protocols in config
        """
        # Clear protocols Config
        self.settings.remove("protocols/")
        # Write new config
        self.settings.beginGroup("protocols")
        for row in range(self.model.rowCount()):
            # Get values
            protocol_name = self.model.data(self.model.index(row,0), QtCore.Qt.DisplayRole) or ""
            command = self.model.data(self.model.index(row,1), QtCore.Qt.DisplayRole) or ""
            args = self.model.data(self.model.index(row,2), QtCore.Qt.DisplayRole) or ""
            clip = int(self.model.data(self.model.index(row,3), QtCore.Qt.CheckStateRole) or 0)
            tooltip = int(self.model.data(self.model.index(row,4), QtCore.Qt.CheckStateRole) or 0)
            # Write values in config
            self.settings.beginGroup(protocol_name)
            self.settings.setValue("command", command)
            self.settings.setValue("args", args)
            self.settings.setValue("clip", clip)
            self.settings.setValue("tooltip", tooltip)
            self.settings.endGroup()
        self.settings.endGroup()
        # Save config
        self.settings.saveConfig()
        # Close dialog
        self.accept()

    def setGeometries(self):
        """
            Set table properties
        """
        # Get horizontal header
        h = self.protocol_list.horizontalHeader()
        # Set headers behaviors
        h.setSectionResizeMode(0, QtWidgets.QHeaderView.Fixed)
        h.setSectionResizeMode(1, QtWidgets.QHeaderView.Stretch)
        h.setStretchLastSection(0)
        # Set size
        self.protocol_list.setColumnWidth(0,100)
        self.protocol_list.setColumnWidth(2,300)
        # Hide vertical hearder
        h = self.protocol_list.verticalHeader()
        h.hide()

class ProtocolView(QtWidgets.QTableView):
    def __init__(self, parent=None):
        QtWidgets.QTableView.__init__(self, parent)
        self.parent = parent

        self.clicked.connect(self.select_bin)


    def select_bin(self, index):
        if index.column() == 1:
            get_file_dialog = QtWidgets.QFileDialog(self)
            get_file_dialog.setAcceptMode(QtWidgets.QFileDialog.AcceptOpen)
            bin_file_name = get_file_dialog.getOpenFileName()
            selected_protocol = self.model().protocols[index.row()]
            self.model().setData(index, bin_file_name)
        

class ProtocolModel(QtGui.QStandardItemModel):
    def __init__(self, parent=None):
        QtGui.QStandardItemModel.__init__(self, parent)
        self.parent = parent
        # List of protocol
        self.protocols = []
        # Header <=> protocol attribute
        self.columns = [
                        "name",
                        "command",
                        "args",
                        "clip",
                        "tooltip",
                        ]

    def setHeaders(self):
        self.setColumnCount(5)
        self.setRowCount(0)
        self.setHeaderData(0, QtCore.Qt.Horizontal, "Protocol")
        self.setHeaderData(1, QtCore.Qt.Horizontal, "Command")
        self.setHeaderData(2, QtCore.Qt.Horizontal, "Arguments")
        self.setHeaderData(3, QtCore.Qt.Horizontal, "Pass to Clip")
        self.setHeaderData(4, QtCore.Qt.Horizontal, "Show tooltip")

    def addProtocol(self, protocol=None, command=None, args=None, clip=QtCore.Qt.Unchecked, tooltip=QtCore.Qt.Unchecked):
        # Create new item
        # Save protocol in protocol list
        self.protocols.append(Protocol(protocol, command, args, clip, tooltip))
        # Add it to the view
        self.insertRow(self.rowCount())

    def delProtocol(self):
        """
            Delete selected row
        """
        # Delete current row
        if self.parent.protocol_list.selectedIndexes():
            selected_row = self.parent.protocol_list.selectedIndexes()[0]
            self.removeRows(selected_row.row(), 1)
            del self.protocols[selected_row.row()]

    def flags(self, index):
        f = QtCore.QAbstractTableModel.flags(self,index)
        if index.column() == 3 or index.column() == 4:
            f |= QtCore.Qt.ItemIsUserCheckable
        else:
            f |= QtCore.Qt.ItemIsEditable
        return f

    def data(self, index, role):
        # if index is not valid
        if not index.isValid():
            return None
        # if protocols is empty
        if not self.protocols:
            return None

        protocol = self.protocols[index.row()] 

        # get value of the checkbox
        if role == QtCore.Qt.CheckStateRole:
            if index.column() == 3 or index.column() == 4:
                attrName = self.columns[index.column()]
                value = getattr(protocol, attrName) 
                return value

        # get value of protocol name and command and args
        if role in [QtCore.Qt.EditRole, QtCore.Qt.DisplayRole]:
            if index.column() == 0 or index.column() == 1 \
               or index.column() == 2:
                attrName = self.columns[index.column()]
                value = getattr(protocol, attrName)
                return value

        return None

    def setData(self, index, value, role=None):
        # if index is not valid
        if not index.isValid():
            return False
        # if protocols is empty
        if not self.protocols:
            return False

        # Get protocol item
        protocol = self.protocols[index.row()]

        # Set attributes
        attrName = self.columns[index.column()]
        result = protocol.setData(value, attrName)

        if result:
            self.dataChanged.emit(index, index)

        return result


class Protocol(QtCore.QObject):
    def __init__(self, name=None, command=None, args=None, clip=QtCore.Qt.Unchecked, tooltip=QtCore.Qt.Unchecked):
        """
            Item protocol which is used to show and
            set parameters
        """
        self.name = name
        self.command = command
        self.args = args
        self.clip = clip
        self.tooltip = tooltip

    def setData(self, value, attr):
        """
            Set attributes
        """
        if attr in ["tooltip", "clip"]:
            try:
                setattr(self, attr, int(value))
                return True
            except (TypeError, ValueError):
                return False
        elif attr in ["name", "command", "args"]:
            value = str(value) if value is not None else ""
            if value:
                setattr(self, attr, value)
                return True
        return False
