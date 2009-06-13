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
#token = getAuth()


class InfoDock(QtGui.QDockWidget):
    def __init__(self, parent=None ):
        QtGui.QDockWidget.__init__(self, "Service", parent)
        self.parent = parent
        self.info = Info()
        self.setWidget(self.info)
        global token

    def showInformations(self, customerid, machineid=None, serviceid=None):
        """
            Show services informations
        """
        # Set New object
        customer = None
        machine = None
        service = None
        # Set a new model
        self.info.model.clear()
        self.info.model.setHeaders()

        customer = getCustomer(customerid)
#        customer = token.vault.customer.get(token.authtok, customerid)
        if machineid:
            machine = getMachine(machineid)
#            machine = token.vault.machine.get(token.authtok, machineid)
            if serviceid:
                service = getService(serviceid)
#                service = token.vault.service.get(token.authtok, serviceid)
        self.info.model.showEditableInformations(customer, machine, service)
        self.info.showInformations(customer, machine, service)
 

class Info(QtGui.QWidget):
    def __init__(self, parent=None ):
        QtGui.QWidget.__init__(self, parent)
        self.parent = parent

        # QlineEdits
        self.tree = InfoTree()
        self.reinit = QtGui.QPushButton(self.tr("Reinitialize"))
        self.save = QtGui.QPushButton(self.tr("Save"))
        self.info_box = QtGui.QGroupBox()
        self.machineLabel = QtGui.QLabel(self.tr("Machine : "))
        self.idLabel = QtGui.QLabel(self.tr("Id : "))
        self.metadataLabel = QtGui.QLabel(self.tr("Metadata"))
#        self.groupslist = QtGui.QLineEdit()
        self.model = InfoModel(self)
        self.tree.setModel(self.model)

        button_layout = QtGui.QHBoxLayout()
        button_layout.addWidget(self.reinit)
        button_layout.addWidget(self.save)

        # Positionning items
        ## Groups groupbox
        gridLayout = QtGui.QGridLayout()
        gridLayout.addWidget(self.idLabel,0,0)
        gridLayout.addWidget(self.machineLabel,1,0)
        gridLayout.addWidget(self.metadataLabel,2,0)
        self.info_box.setLayout(gridLayout)

        # QGridLayout
        mainLayout = QtGui.QGridLayout()
        mainLayout.addWidget(self.tree,0,0)
        mainLayout.addLayout(button_layout,1,0)
        mainLayout.addWidget(self.info_box,2,0,1,2)

        # Geometries
        self.setWindowTitle(self.tr("Service Informations"))

        # Show window
        self.setLayout(mainLayout)

    def showInformations(self, customer, machine=None, service=None):
        if service:
            for key, data in service["service"].items():
                if key in ["id"]:
                    self.idLabel.setText(self.tr("Id : %s" % unicode(data)))
        elif machine:
            for key, data in machine["machine"].items():
                if key in ["id"]:
                    self.idLabel.setText(self.tr("Id : %s" % unicode(data)))
        elif customer:
            for key, data in customer["customer"].items():
                if key in ["id"]:
                    self.idLabel.setText(self.tr("Id : %s" % unicode(data)))

class InfoTree(QtGui.QTreeView):
    def __init__(self, parent=None):
        QtGui.QTreeView.__init__(self, parent)
        self.parent = parent


class InfoModel(QtGui.QStandardItemModel):
    def __init__(self, parent=None):
        QtGui.QStandardItemModel.__init__(self, 0, 2, parent)
        self.parent = parent
        self.setHeaders()
        global token

    def setHeaders(self):
        self.setColumnCount(2)
        self.setRowCount(0)
        self.setHeaderData(0, QtCore.Qt.Horizontal, QtCore.QVariant("Name"))
        self.setHeaderData(1, QtCore.Qt.Horizontal, QtCore.QVariant("Value"))

    def showEditableInformations(self, customer, machine=None, service=None):
        """
            Show services informations
        """
        if service: 
            for key, data in service["service"].items():
                if key in ["url", "notes", "group_id", "parent_service_id"]:
                    self.insertRow(0)
                    self.setData(self.index(0, 1), QtCore.QVariant(data))
                    self.setData(self.index(0, 0), QtCore.QVariant(key))
        elif machine:
            for key, data in machine["machine"].items():
                if key in ["name", "ip", "fqdn", "location", "notes"]:
                    self.insertRow(0)
                    self.setData(self.index(0, 1), QtCore.QVariant(data))
                    self.setData(self.index(0, 0), QtCore.QVariant(key))
        elif customer:
            for key, data in customer["customer"].items():
                if key in ["name", ]:
                    self.insertRow(0)
                    self.setData(self.index(0, 1), QtCore.QVariant(data))
                    self.setData(self.index(0, 0), QtCore.QVariant(key))

