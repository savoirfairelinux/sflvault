#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
#    sflvault_qt/docs/infodock.py
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
from PyQt4 import QtCore, QtGui
import re
from PyQt4.QtCore import Qt
import sflvault
from sflvault.client import SFLvaultClient
import shutil
import os

from sflvault.clientqt.lib.auth import *


class InfoDock(QtGui.QDockWidget):
    def __init__(self, parent=None ):
        QtGui.QDockWidget.__init__(self, parent)
        self.parent = parent
        self.info = Info(self)
        self.setWidget(self.info)
        self.setWindowTitle(self.tr("Informations"))

        ## Check visibility
        QtCore.QObject.connect(self, QtCore.SIGNAL("visibilityChanged (bool)"), self.parent.menubar.checkDockBoxes)

    def showInformations(self, customerid, machineid=None, serviceid=None):
        """
            Show services informations
        """
        # Save item ids
        self.customerid = customerid
        self.machineid = machineid
        self.serviceid = serviceid
        # Set New object
        self.customer = None
        self.machine = None
        self.service = None
        # Set a new model
        self.info.model.clear()
        self.info.model.setHeaders()

        self.customer = getCustomer(customerid)
        self.setWindowTitle("Customer")
        if machineid and self.customer:
            self.machine = getMachine(machineid)
            self.setWindowTitle("Machine")
            if self.machine and serviceid:
                self.service = getService(serviceid, True)
                self.setWindowTitle("Service")
                if not self.service:
                    self.setWindowTitle("Informations")
                    return None
            elif not self.machine:
                self.setWindowTitle("Informations")
                return None
        elif not self.customer:
            self.setWindowTitle("Informations")
            return None
        self.info.model.attributes = []
        self.info.edit_info_bar.hide()
        self.info.save.hide()
        self.info.reinit.hide()
        self.info.model.showEditableInformations(self.customer, self.machine, self.service)
        self.info.showInformations(self.customer, self.machine, self.service)


class ModificationStatus(QtGui.QWidget):
    def __init__(self, parent=None):
        QtGui.QWidget.__init__(self, parent)
        self.parent = parent

        self.status = QtGui.QLabel("Edition Mode")
        # QGridLayout
        mainLayout = QtGui.QGridLayout()
        mainLayout.addWidget(self.status,0,0)
        mainLayout.setMargin(0)
        mainLayout.setSpacing(0)
        
        # Show window
        self.setLayout(mainLayout)
        self.hide()

class Info(QtGui.QWidget):
    def __init__(self, parent=None):
        QtGui.QWidget.__init__(self, parent)
        self.parent = parent

        self.serviceList = {}
        self.machineList = {}
        self.customerList = {}
        self.serviceListTitle = {}
        self.machineListTitle = {}
        self.customerListTitle = {}

        # QlineEdits
        self.tree = InfoTree(self)
        self.reinit = QtGui.QPushButton(self.tr("Reinitialize"))
        self.reinit.hide()
        self.save = QtGui.QPushButton(self.tr("Save"))
        self.save.hide()
        self.info_box = QtGui.QGroupBox()

        # Info bar
        self.edit_info_bar = ModificationStatus(self)

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
        #self.serviceListTitle["metadata"] = QtGui.QLabel(self.tr("Metadata :"))
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
        mainLayout.addWidget(self.edit_info_bar,1,0,1,2)
        mainLayout.addLayout(button_layout,2,0)
        mainLayout.addWidget(self.info_box,3,0,1,2)

        # Geometries
        self.setWindowTitle(self.tr("Items Informations"))

        # Show window
        self.setLayout(mainLayout)

        # Signals
        QtCore.QObject.connect(self.reinit, QtCore.SIGNAL("clicked()"), self.reloadInformation)
        QtCore.QObject.connect(self.save, QtCore.SIGNAL("clicked()"), self.editItem)


    # Back to actual informations
    def reloadInformation(self):
        # Set a new model
        self.model.clear()
        self.model.setHeaders()
        self.model.showEditableInformations(self.parent.customer, self.parent.machine, self.parent.service)
        self.showInformations(self.parent.customer, self.parent.machine, self.parent.service)
        # Hide edit mode
        self.edit_info_bar.hide()
        self.save.hide()
        self.reinit.hide()

    def editItem(self):
        # if item is a customer
        if self.model.mode == "customer":
            custid = self.parent.customerid
            cust_info = {}
            # Create dict
            for attribute in self.model.attributes:
                try:
                    new_value = int(attribute.values()[0])
                except:
                    new_value = attribute.values()[0]
                cust_info[attribute.keys()[0]] = new_value
            # Save it
            editCustomer(custid, cust_info)
        # if item is a machine
        elif self.model.mode == "machine":
            machid = self.parent.machineid
            mach_info = {}
            # Create dict
            for attribute in self.model.attributes:
                try:
                    new_value = int(attribute.values()[0])
                except:
                    new_value = attribute.values()[0]
                mach_info[attribute.keys()[0]] = new_value
            # Save it
            editMachine(machid, mach_info)
        # if item is a service
        elif self.model.mode == "service":
            servid = self.parent.serviceid
            serv_info = {}
            # Create dict
            for attribute in self.model.attributes:
                try:
                    new_value = int(attribute.values()[0])
                except:
                    new_value = attribute.values()[0]
                serv_info[attribute.keys()[0]] = new_value
            # Save it
            editService(servid, serv_info)
        # Hide edit mode
        self.edit_info_bar.hide()
        self.save.hide()
        self.reinit.hide()
        # Reload Tree
        self.parent.parent.search(None)


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
            # Show service, machine and customer
            self.showMachine()
            self.showCustomer()
            self.showService()
            for key, data in service["services"][-1].items():
                if key in ["id", ]:
                    # Show and hide label
                    self.serviceList["id"].show()
                    self.serviceList["id"].setText(unicode("s#" + str(data)))
                    self.serviceListTitle["id"].show()
            # show machine information
            for key, data in machine["machine"].items():
                if not key in ["customer_id", "id", ]:
                    self.machineList[key].setText(unicode(data))
                # Show "#" for id
                elif key in ["id", ]:
                    self.machineList[key].setText(unicode("m#" + str(data)))
            # show customer information
            for key, data in customer["customer"].items():
                # Show "#" for id
                if key in ["id", ]:
                    self.customerList[key].setText(unicode("c#" + str(data)))
                else:
                    self.customerList[key].setText(unicode(data))
        elif machine:
            # Hide service and machine, show customer
            self.showCustomer()
            self.hideService()
            self.hideMachine()
            # show machine id
            for key, data in machine["machine"].items():
                if key in ["id", ]:
                    # Show and hide label
                    self.machineList["id"].show()
                    self.machineList["id"].setText(unicode("m#" + str(data)))
                    self.machineListTitle["id"].show()
            # show customer information
            for key, data in customer["customer"].items():
                # Show "#" for id
                if key in ["id", ]:
                    self.customerList[key].setText(unicode("c#" + str(data)))
                else:
                    self.customerList[key].setText(unicode(data))
        elif customer:
            # Hide all
            self.hideService()
            self.hideMachine()
            self.hideCustomer()
            # Show only customer id
            for key, data in customer["customer"].items():
                # Show "#" for id
                if key in ["id", ]:
                    # Show and hide label
                    self.customerList[key].show()
                    self.customerList[key].setText(unicode("c#" + str(data)))
                    self.customerListTitle[key].show()


class InfoTree(QtGui.QTreeView):
    def __init__(self, parent=None):
        QtGui.QTreeView.__init__(self, parent)
        self.parent = parent
        self.setRootIsDecorated(False)
        # Get Editor
        Editor = self.itemDelegate()
        QtCore.QObject.connect(Editor, QtCore.SIGNAL("commitData (QWidget *)"), self.editorClosed)

    def editorClosed(self, editor):
        self.parent.edit_info_bar.show()
        self.parent.save.show()
        self.parent.reinit.show()

class InfoModel(QtGui.QStandardItemModel):
    def __init__(self, parent=None):
        QtGui.QStandardItemModel.__init__(self, 0, 2, parent)
        self.parent = parent
        self.setHeaders()
        self.mode = None
        self.attributes = []

    def setHeaders(self):
        self.setColumnCount(2)
        self.setRowCount(0)
        self.setHeaderData(0, QtCore.Qt.Horizontal, QtCore.QVariant("Name"))
        self.setHeaderData(1, QtCore.Qt.Horizontal, QtCore.QVariant("Value"))

    def showEditableInformations(self, customer, machine=None, service=None):
        """
            Show services informations
        """
        self.attributes = []
        if service:
            self.mode = "service"
            for key, data in service["services"][-1].items():
                if key in ["url", "notes", "group_id", "parent_service_id", "groups_list"]:
                    if type(data) == list:
                        data = unicode(u" | ".join([ group[1] + "(g#" + unicode(group[0]) + ")"  for group in data]))
                    self.insertRow(0)
                    self.attributes.append({key: data})
        elif machine:
            self.mode = "machine"
            for key, data in machine["machine"].items():
                if key in ["name", "ip", "fqdn", "location", "notes"]:
                    self.insertRow(0)
                    self.attributes.append({key: data})
        elif customer:
            self.mode = "customer"
            for key, data in customer["customer"].items():
                if key in ["name", ]:
                    self.insertRow(0)
                    self.attributes.append({key: data})

    def flags(self, index):
        f = QtCore.QAbstractTableModel.flags(self,index)
        if index.column() == 1:
            f |= QtCore.Qt.ItemIsEditable
        return f


    def data(self, index, role):
        # if index is not valid
        if not index.isValid():
            return QtCore.QVariant()
        # if attributes is empty
        if not self.attributes:
            return QtCore.QVariant()

        try:
            attribute = self.attributes[index.row()]
        except IndexError, e:
            return  QtCore.QVariant()

        # get value of protocol name and command
        if role in [QtCore.Qt.EditRole, QtCore.Qt.DisplayRole]:
            if index.column() == 0:
                value = attribute.keys()[0]
                return QtCore.QVariant(value)
            if index.column() == 1:
                value = attribute.values()[0]
                return QtCore.QVariant(value)

        return QtCore.QVariant()


    def setData(self, index, value, role=QtCore.Qt.DisplayRole):
        # if index is not valid
        if not index.isValid():
            return QtCore.QVariant()
        # if attributes is empty
        if not self.attributes:
            return QtCore.QVariant()

         # Get attribute
        attribute = self.attributes[index.row()]
        # Get attribute name
        key = attribute.keys()[0]
        # Get New value
        new_value, bool = value.toInt()
        if not bool:
            new_value = unicode(value.toString())
        # Set attribute with new value
        try:
            attribute[key] = new_value
            self.dataChanged.emit(index, index)
            return True
        except:    
            return False

