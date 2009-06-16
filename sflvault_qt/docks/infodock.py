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
        if machineid and customer:
            machine = getMachine(machineid)
            if serviceid and customer:
                service = getService(serviceid)
                if not service:
                    return None
            else:
                return None
        else:
            return None
        self.info.model.showEditableInformations(customer, machine, service)
        self.info.showInformations(customer, machine, service)
 

class Info(QtGui.QWidget):
    def __init__(self, parent=None ):
        QtGui.QWidget.__init__(self, parent)
        self.parent = parent

        self.serviceList = {}
        self.machineList = {}
        self.customerList = {}
        self.serviceListTitle = {}
        self.machineListTitle = {}
        self.customerListTitle = {}

        # QlineEdits
        self.tree = InfoTree()
        self.reinit = QtGui.QPushButton(self.tr("Reinitialize"))
        self.save = QtGui.QPushButton(self.tr("Save"))
        self.info_box = QtGui.QGroupBox()

        self.model = InfoModel(self)
        self.tree.setModel(self.model)

        button_layout = QtGui.QHBoxLayout()
        button_layout.addWidget(self.reinit)
        button_layout.addWidget(self.save)

        self.clearService()
        self.clearMachine()
        self.clearCustomer()

        # Positionning items
        ## Groups groupbox
        gridLayout = QtGui.QGridLayout()

        # Label Title
        ## Service
        self.serviceListTitle["id"] = QtGui.QLabel(self.tr("Id :"))
        self.serviceListTitle["metadata"] = QtGui.QLabel(self.tr("Metadata :"))
        ## Machine
        self.machineListTitle["fqdn"] = QtGui.QLabel(self.tr("Machine FQDN :"))
        self.machineListTitle["id"] = QtGui.QLabel(self.tr("Machine Id :"))
        self.machineListTitle["ip"] = QtGui.QLabel(self.tr("Machine IP :"))
        self.machineListTitle["location"] = QtGui.QLabel(self.tr("Machine Location :"))
        self.machineListTitle["name"] = QtGui.QLabel(self.tr("Machine Name :"))
        self.machineListTitle["notes"] = QtGui.QLabel(self.tr("Machine Notes :"))
        ## Customer
        self.customerListTitle["id"] = QtGui.QLabel(self.tr("Customer Id :"))
        self.customerListTitle["name"] = QtGui.QLabel(self.tr("Customer Name :"))
        # Register Qlabels
        i = 0
        for label in self.serviceListTitle.values():
            gridLayout.addWidget(label, i, 0)
            i = i + 1;
        for label in self.machineListTitle.values():
            gridLayout.addWidget(label, i, 0)
            i = i + 1;
        for label in self.customerListTitle.values():
            gridLayout.addWidget(label, i, 0)
            i = i + 1;

        # Label information
        ## Service
        self.serviceList["id"] = QtGui.QLabel()
        self.serviceList["metadata"] = QtGui.QLabel()
        ## Machine
        self.machineList["id"] = QtGui.QLabel()
        self.machineList["name"] = QtGui.QLabel()
        self.machineList["ip"] = QtGui.QLabel()
        self.machineList["fqdn"] = QtGui.QLabel()
        self.machineList["location"] = QtGui.QLabel()
        self.machineList["notes"] = QtGui.QLabel()
        ## Customer
        self.customerList["id"] = QtGui.QLabel()
        self.customerList["name"] = QtGui.QLabel()
        # Register Qlabels
        i = 0
        for label in self.serviceList.values():
            label.setWordWrap(True)
            gridLayout.addWidget(label, i, 1)
            i = i + 1;
        for label in self.machineList.values():
            label.setWordWrap(True)
            gridLayout.addWidget(label, i, 1)
            i = i + 1;
        for label in self.customerList.values():
            label.setWordWrap(True)
            gridLayout.addWidget(label, i, 1)
            i = i + 1;

        self.info_box.setLayout(gridLayout)

        # QGridLayout
        mainLayout = QtGui.QGridLayout()
        mainLayout.addWidget(self.tree,0,0)
        mainLayout.addLayout(button_layout,1,0)
        mainLayout.addWidget(self.info_box,2,0,1,2)

        # Geometries
        self.setWindowTitle(self.tr("Items Informations"))

        # Show window
        self.setLayout(mainLayout)

    # Show
    def showService(self):
        for label in self.serviceList.values():
            label.show()
        for label in self.serviceListTitle.values():
            label.show()

    def showMachine(self):
        for label in self.machineList.values():
            label.show()
        for label in self.machineListTitle.values():
            label.show()

    def showCustomer(self):
        for label in self.customerList.values():
            label.show()
        for label in self.customerListTitle.values():
            label.show()

    # Hide
    def hideService(self):
        for label in self.serviceList.values():
            label.hide()
        for label in self.serviceListTitle.values():
            label.hide()

    def hideMachine(self):
        for label in self.machineList.values():
            label.hide()
        for label in self.machineListTitle.values():
            label.hide()

    def hideCustomer(self):
        for label in self.customerList.values():
            label.hide()
        for label in self.customerListTitle.values():
            label.hide()

    # Clear
    def clearService(self):
        for label in self.serviceList.values():
            label.clear()
        for label in self.serviceListTitle.values():
            label.clear()

    def clearMachine(self):
        for label in self.machineList.values():
            label.clear()
        for label in self.machineListTitle.values():
            label.clear()

    def clearCustomer(self):
        for label in self.customerList.values():
            label.clear()
        for label in self.customerListTitle.values():
            label.clear()

    def showInformations(self, customer, machine=None, service=None):
        if service:
            for key, data in service["service"].items():
                if key in ["id"]:
                    # Show and hide label
                    self.showMachine()
                    self.showCustomer()
                    self.showService()
                    self.serviceList["id"].show()
                    self.serviceList["id"].setText(unicode(data))
                    self.serviceListTitle["id"].show()
            # show machine information
            for key, data in machine["machine"].items():
                if not key in ["customer_id"]:
                    self.machineList[key].setText(unicode(data))
            # show customer information
            for key, data in customer["customer"].items():
                self.customerList[key].setText(unicode(data))           
        elif machine:
            for key, data in machine["machine"].items():
                if key in ["id"]:
                    # Show and hide label
                    self.hideService()
                    self.hideMachine()
                    self.machineList["id"].show()
                    self.machineList["id"].setText(unicode(data))
                    self.machineListTitle["id"].show()
            # show customer information
            for key, data in customer["customer"].items():
                self.customerList[key].setText(unicode(data))
        elif customer:
            for key, data in customer["customer"].items():
                if key in ["id", "name"]:
                    # Show and hide label
                    self.hideService()
                    self.hideMachine()
                    self.customerList[key].show()
                    self.customerList[key].setText(unicode(data))
                    self.customerListTitle[key].show()


class InfoTree(QtGui.QTreeView):
    def __init__(self, parent=None):
        QtGui.QTreeView.__init__(self, parent)
        self.parent = parent
        self.setRootIsDecorated(False)


class InfoModel(QtGui.QStandardItemModel):
    def __init__(self, parent=None):
        QtGui.QStandardItemModel.__init__(self, 0, 2, parent)
        self.parent = parent
        self.setHeaders()

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

