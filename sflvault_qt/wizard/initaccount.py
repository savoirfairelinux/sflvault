#!/usr/bin/env python
# -*- coding: UTF-8 -*-
#
#    sflvault_qt/wizard/initaccount.py
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
from lib.auth import *
import shutil
import os


class InitAccount(QtGui.QWizard):
    def __init__(self, parent=None):
        QtGui.QWizard.__init__(self, parent)
        self.parent = parent

        page1 = Page1(self)
        page2 = Page2(self)
        page3 = Page3(self)
        self.addPage(page1)
        self.addPage(page2)
        self.addPage(page3)
        self.setWindowTitle("Account activation")
        self.show()


class Page1(QtGui.QWizardPage):
    def __init__(self, parent=None):
        QtGui.QWizard.__init__(self, parent)
        self.parent = parent

        self.setTitle("Account Activation")

        label = QtGui.QLabel("This wizard will activate your account."
                )
        label.setWordWrap(True)

        layout = QtGui.QVBoxLayout()
        layout.addWidget(label)
        self.setLayout(layout)


class Page2(QtGui.QWizardPage):
    def __init__(self, parent=None):
        QtGui.QWizardPage.__init__(self, parent)
        self.parent = parent
        self.setTitle("Initialize your vault account")
        self.setSubTitle("Fill this form")
        self.setCommitPage(True)
        
        username_label = QtGui.QLabel(self.tr("&Username"))
        self.username = QtGui.QLineEdit(os.getenv('USER'))
        username_label.setBuddy(self.username)

        address_label = QtGui.QLabel(self.tr("&Vault URL"))
        self.address = QtGui.QLineEdit()
        self.address.setText("http://localhost:5000/vault/rp")
        address_label.setBuddy(self.address)

        password1_label = QtGui.QLabel(self.tr("&Password"))
        self.password1 = QtGui.QLineEdit()
        self.password1.setEchoMode(QtGui.QLineEdit.Password)
        password1_label.setBuddy(self.password1)

        password2_label = QtGui.QLabel(self.tr("Confirm your password"))
        self.password2 = QtGui.QLineEdit()
        self.password2.setEchoMode(QtGui.QLineEdit.Password)
        password2_label.setBuddy(self.password2)

        layout = QtGui.QGridLayout(self)
        layout.addWidget(username_label,0,0)
        layout.addWidget(self.username,0,1)
        layout.addWidget(address_label,1,0)
        layout.addWidget(self.address,1,1)
        layout.addWidget(password1_label,2,0)
        layout.addWidget(self.password1,2,1)
        layout.addWidget(password2_label,3,0)
        layout.addWidget(self.password2,3,1)

        self.setLayout(layout)
        self.registerField("username", self.username)
        self.registerField("address", self.address)
        self.registerField("password1*", self.password1)
        self.registerField("password2*", self.password2)

    def validatePage(self):
        if self.password2.text().compare(self.password1.text()):
            error = QtGui.QMessageBox(QtGui.QMessageBox.Critical, "Password error", "Passwords don't match")
            error.exec_()
            return False
        elif not registerAccount(unicode(self.username.text()), unicode(self.address.text()), unicode(self.password1.text())):
            return False
        self.parent.parent.settings.sync()
        return True


class Page3(QtGui.QWizardPage):
    def __init__(self, parent=None):
        QtGui.QWizardPage.__init__(self, parent)
        self.parent = parent

        self.setTitle("Account activation successfully")

        label = QtGui.QLabel("You account is now activated."
                            "You can now connect to the vault."
                            )
        label.setWordWrap(True)

        layout = QtGui.QVBoxLayout()
        layout.addWidget(label)
        self.setFinalPage(True)
        self.setLayout(layout)
