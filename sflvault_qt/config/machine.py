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

class MachineWidget(QtGui.QDialog):
    def __init__(self, macjid=None, parent=None):
        QtGui.QDialog.__init__(self, parent)
        self.parent = parent
        self.settings = self.parent.settings
        self.protocols = {}

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

        self.save = QtGui.QPushButton(self.tr("Add machine"))
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
        self.show()

    def accept(self):
        name = unicode(self.name.text())
        custid, bool = self.customer.itemData(self.customer.currentIndex()).toInt()
        fqdn = unicode(self.fqdn.text())
        address = unicode(self.address.text())
        location = unicode(self.location.text())
        notes = unicode(self.notes.text())
        addMachine(name, custid, fqdn, address, location, notes)
        self.parent.search(None)
        self.done(1)
