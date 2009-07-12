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

class CustomerWidget(QtGui.QDialog):
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
