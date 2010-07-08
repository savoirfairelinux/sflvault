#!/usr/bin/env python
# -*- coding: UTF-8 -*-
#
#    sflvault_qt/config/machine.py
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


class DeleteMachineWidget(QtGui.QMessageBox):
    def __init__(self, machid=None, parent=None):
        QtGui.QMessageBox.__init__(self, parent)
        self.parent = parent
        # Check if a line is selected
        if not machid:
            return None
        self.machid = machid
        # Test if machine exist
        machine = getMachine(machid)
        if not "machine" in machine:
            return None
        # Set windows
        self.setIcon(QtGui.QMessageBox.Question)
        self.ok = self.addButton(QtGui.QMessageBox.Ok)
        self.cancel = self.addButton(QtGui.QMessageBox.Cancel)
        self.setText(self.tr("Do you want to delete %s" % machine["machine"]["name"]))

        # SIGNALS
        self.connect(self.ok, QtCore.SIGNAL("clicked()"), self, QtCore.SLOT("accept()"))
        self.connect(self.cancel, QtCore.SIGNAL("clicked()"), self, QtCore.SLOT("reject()"))

    def accept(self):
        # Delete machine
        status = delMachine(self.machid)
        if status:
            # reload tree
            self.parent.search(None)
            self.done(1)


class EditMachineWidget(QtGui.QDialog):
    def __init__(self, machid=None, custid=None, parent=None):
        QtGui.QDialog.__init__(self, parent)
        self.parent = parent
        self.settings = self.parent.settings
        self.machid = machid
        self.custid = custid
        self.mode = "add"

        # Load gui items
        groupbox = QtGui.QGroupBox()
        self.nameLabel = QtGui.QLabel(self.tr("Machine Name"))
        self.name = QtGui.QLineEdit()
        self.customerLabel = QtGui.QLabel(self.tr("Customer"))
        self.customer = QtGui.QComboBox()
        self.fqdnLabel = QtGui.QLabel(self.tr("FQDN"))
        self.fqdn = QtGui.QLineEdit()
        self.addressLabel = QtGui.QLabel(self.tr("Address"))
        self.address = QtGui.QLineEdit()
        self.locationLabel = QtGui.QLabel(self.tr("Location"))
        self.location = QtGui.QLineEdit()
        self.notesLabel = QtGui.QLabel(self.tr("Notes"))
        self.notes = QtGui.QLineEdit()

        self.save = QtGui.QPushButton(self.tr("Save machine"))
        self.cancel = QtGui.QPushButton(self.tr("Cancel"))

        # Positionning items
        ## Groups groupbox
        gridLayout = QtGui.QGridLayout()
        gridLayout.addWidget(self.nameLabel, 0, 0)
        gridLayout.addWidget(self.name, 0, 1)
        gridLayout.addWidget(self.customerLabel, 1, 0)
        gridLayout.addWidget(self.customer, 1, 1)
        gridLayout.addWidget(self.fqdnLabel, 2, 0)
        gridLayout.addWidget(self.fqdn, 2, 1)
        gridLayout.addWidget(self.addressLabel, 3, 0)
        gridLayout.addWidget(self.address, 3, 1)
        gridLayout.addWidget(self.locationLabel, 4, 0)
        gridLayout.addWidget(self.location, 4, 1)
        gridLayout.addWidget(self.notesLabel, 5, 0)
        gridLayout.addWidget(self.notes, 5, 1)
        gridLayout.addWidget(self.save, 6, 0)
        gridLayout.addWidget(self.cancel,6,1)
        groupbox.setLayout(gridLayout)

        mainLayout = QtGui.QGridLayout()
        mainLayout.addWidget(groupbox,0,0)
        self.setLayout(mainLayout)

        self.setWindowTitle(self.tr("Add machine"))

        # SIGNALS
        self.connect(self.save, QtCore.SIGNAL("clicked()"), self, QtCore.SLOT("accept()"))
        self.connect(self.cancel, QtCore.SIGNAL("clicked()"), self, QtCore.SLOT("reject()"))

    def exec_(self):
        # get customer lists
        customers = listCustomers()
        for customer in customers["list"]:
            self.customer.addItem(customer['name'] +" - c#" + unicode(customer['id']) , QtCore.QVariant(customer['id']))

        if self.machid:
            # Fill fields for edit mode
            machine = getMachine(self.machid)
            informations = machine["machine"]
            self.name.setText(informations["name"])
            self.customer.setCurrentIndex(self.customer.findData(
                                QtCore.QVariant(informations["customer_id"])))
            self.fqdn.setText(informations["fqdn"])
            self.address.setText(informations["ip"])
            self.location.setText(informations["location"])
            self.notes.setText(informations["notes"])
            # Set mode and texts
            self.mode = "edit"
            self.setWindowTitle(self.tr("Edit machine"))

        if self.custid:
            self.customer.setCurrentIndex(self.customer.findData(QtCore.QVariant(self.custid)))

        self.show()

    def accept(self):
        # Buil dict to transmit to the vault
        machine_info = {"name": None,
                        "customer_id": None,
                        "fqdn": None,
                        "ip": None,
                        "location": None,
                        "notes": None,
                        }
        # Fill it
        machine_info["name"] = unicode(self.name.text())
        machine_info["customer_id"], bool =\
                self.customer.itemData(self.customer.currentIndex()).toInt()
        machine_info["fqdn"] = unicode(self.fqdn.text())
        machine_info["ip"] = unicode(self.address.text())
        machine_info["location"] = unicode(self.location.text())
        machine_info["notes"] = unicode(self.notes.text())
        if self.mode == "add":
            # Add a new machine
            addMachine(machine_info["name"], machine_info["customer_id"],
                    machine_info["fqdn"], machine_info["ip"],
                    machine_info["location"], machine_info["notes"])
        elif self.mode == "edit":
            # Edit a machine
            editMachine(self.machid, machine_info)
        # reload tree
        self.parent.search(None)
        self.done(1)
