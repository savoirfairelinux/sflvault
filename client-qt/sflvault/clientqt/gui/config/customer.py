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
from PyQt4 import QtCore, QtGui
import re
from PyQt4.QtCore import Qt
import sflvault
from sflvault.client import SFLvaultClient
import shutil
import os

from sflvault.clientqt.lib.auth import *


class DeleteCustomerWidget(QtGui.QMessageBox):
    def __init__(self, custid=None, parent=None):
        QtGui.QMessageBox.__init__(self, parent)
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
        self.setIcon(QtGui.QMessageBox.Question)
        self.ok = self.addButton(QtGui.QMessageBox.Ok)
        self.cancel = self.addButton(QtGui.QMessageBox.Cancel)
        self.setText(self.tr("Do you want to delete %s" % customer["customer"]["name"]))

        # SIGNALS
        self.connect(self.ok, QtCore.SIGNAL("clicked()"), self, QtCore.SLOT("accept()"))
        self.connect(self.cancel, QtCore.SIGNAL("clicked()"), self, QtCore.SLOT("reject()"))

    def accept(self):
        # Delete customer
        status = delCustomer(self.custid)
        if status:
            # reload tree
            self.parent.search(None)
            self.done(1)
        

class EditCustomerWidget(QtGui.QDialog):
    def __init__(self, custid=None, parent=None):
        QtGui.QDialog.__init__(self, parent)
        self.parent = parent
        self.custid = custid
        self.mode = "add"

        # Load gui items
        groupbox = QtGui.QGroupBox()
        self.nameLabel = QtGui.QLabel(self.tr("Customer Name"))
        self.name = QtGui.QLineEdit()

        self.save = QtGui.QPushButton(self.tr("Save customer"))
        self.cancel = QtGui.QPushButton(self.tr("Cancel"))

        # Positionning items
        ## Groups groupbox
        gridLayout = QtGui.QGridLayout()
        gridLayout.addWidget(self.nameLabel,0,0)
        gridLayout.addWidget(self.name,0,1)
        gridLayout.addWidget(self.save,1,0)
        gridLayout.addWidget(self.cancel,1,1)
        groupbox.setLayout(gridLayout)

        mainLayout = QtGui.QGridLayout()
        mainLayout.addWidget(groupbox,0,0)
        self.setLayout(mainLayout)

        self.setWindowTitle(self.tr("Add customer"))

        # SIGNALS
        self.connect(self.save, QtCore.SIGNAL("clicked()"), self, QtCore.SLOT("accept()"))
        self.connect(self.cancel, QtCore.SIGNAL("clicked()"), self, QtCore.SLOT("reject()"))

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
        customer_info["name"] = unicode(self.name.text())
        if self.mode == "add":
            # Add new customer
            addCustomer(customer_info["name"])
        elif self.mode == "edit":
            # Edit customer
            editCustomer(self.custid, customer_info)
        self.parent.search(None)
        self.done(1)
