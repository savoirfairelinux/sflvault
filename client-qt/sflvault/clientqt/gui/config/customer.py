#!/usr/bin/env python
# -*- coding: UTF-8 -*-
#
#    sflvault_qt/config/customer.py
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

from sflvault.clientqt.lib.auth import *


class DeleteCustomerWidget(QtWidgets.QMessageBox):
    def __init__(self, custid=None, parent=None):
        QtWidgets.QMessageBox.__init__(self, parent)
        self.parent = parent
        # Check if a line is selected
        if not custid:
            return False
        self.custid = custid
        # Test if customer exist
        customer = getCustomer(custid)
        if not "customer" in customer:
            return False
        # Set windows
        self.setIcon(QtWidgets.QMessageBox.Question)
        self.ok = self.addButton(QtWidgets.QMessageBox.Ok)
        self.cancel = self.addButton(QtWidgets.QMessageBox.Cancel)
        self.setText(self.tr("Do you want to delete %s" % customer["customer"]["name"]))

        # SIGNALS
        self.ok.clicked.connect(self.accept)
        self.cancel.clicked.connect(self.reject)

    def accept(self):
        # Delete customer
        status = delCustomer(self.custid)
        if status:
            # reload tree
            self.parent.search(None)
            self.done(1)
        

class EditCustomerWidget(QtWidgets.QDialog):
    def __init__(self, custid=None, parent=None):
        QtWidgets.QDialog.__init__(self, parent)
        self.parent = parent
        self.custid = custid
        self.mode = "add"

        # Load gui items
        groupbox = QtWidgets.QGroupBox()
        self.nameLabel = QtWidgets.QLabel(self.tr("Customer Name"))
        self.name = QtWidgets.QLineEdit()

        self.save = QtWidgets.QPushButton(self.tr("Save customer"))
        self.cancel = QtWidgets.QPushButton(self.tr("Cancel"))

        # Positionning items
        ## Groups groupbox
        gridLayout = QtWidgets.QGridLayout()
        gridLayout.addWidget(self.nameLabel,0,0)
        gridLayout.addWidget(self.name,0,1)
        gridLayout.addWidget(self.cancel,1,0)
        gridLayout.addWidget(self.save,1,1)
        groupbox.setLayout(gridLayout)

        mainLayout = QtWidgets.QGridLayout()
        mainLayout.addWidget(groupbox,0,0)
        self.setLayout(mainLayout)

        self.setWindowTitle(self.tr("Add customer"))

        # SIGNALS
        self.save.clicked.connect(self.accept)
        self.cancel.clicked.connect(self.reject)

    def exec_(self):
        # Set field if is an edit
        if self.custid:
            customer = getCustomer(self.custid)
            self.name.setText(customer["customer"]["name"])
            # Set mode to edit
            self.mode = "edit"
            self.setWindowTitle(self.tr("Edit customer"))
        self.show()

    def accept(self):
        customer_info = {"name" : None}
        customer_info["name"] = str(self.name.text())
        if self.mode == "add":
            # Add new customer
            addCustomer(customer_info["name"])
        elif self.mode == "edit":
            # Edit customer
            editCustomer(self.custid, customer_info)
        self.parent.search(None)
        self.done(1)
