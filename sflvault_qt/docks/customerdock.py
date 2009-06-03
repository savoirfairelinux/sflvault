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


from auth import auth
token = auth.getAuth()

class CustomerInfoDock(QtGui.QDockWidget):
    def __init__(self, parent=None, ):
        QtGui.QDockWidget.__init__(self, "Customer", parent)
        self.parent = parent
        self.customerInfo = CustomerInfo()
        self.setWidget(self.customerInfo)
        global token

    def showInformations(self, id):
        """
            Show machines informations
        """
        customer = token.vault.customer.get(token.authtok,id)
        self.customerInfo.name.setText(customer["customer"]["name"])

class CustomerInfo(QtGui.QWidget):
    def __init__(self, parent=None, ):
        QtGui.QWidget.__init__(self, parent)
        self.parent = parent

        # QlineEdits
        self.name = QtGui.QLineEdit()
        self.nameLabel = QtGui.QLabel(self.tr("Name"))

        # QGridLayout
        mainLayout = QtGui.QGridLayout()
        mainLayout.addWidget(self.nameLabel,0,0)
        mainLayout.addWidget(self.name,0,1)

        # Geometries
        self.setWindowTitle(self.tr("Customer Informations"))

        # Show window
        self.setLayout(mainLayout)

        
