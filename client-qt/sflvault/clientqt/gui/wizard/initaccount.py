#!/usr/bin/env python
# -*- coding: utf-8 -*-
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
from savepassword import SavePasswordWizard
from sflvault.clientqt.lib.auth import *
import shutil
import os


class InitAccount(QtGui.QWizard):
    def __init__(self, parent=None):
        """ Wizard to launch user-setup
        """
        QtGui.QWizard.__init__(self, parent)
        self.parent = parent
        # Init Pages
        page1 = Page1(self)
        page2 = Page2(self)
        page3 = Page3(self)
        # Add pages
        self.addPage(page1)
        self.addPage(page2)
        self.addPage(page3)
        self.setWindowTitle("Account activation")
        self.show()


class Page1(QtGui.QWizardPage):
    def __init__(self, parent=None):
        """ Introduction page
        """
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
        """ Form page
        """
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
        self.address.setText("https://localhost:5000/vault/rpc")
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
        # Register fields
        self.registerField("username", self.username)
        self.registerField("address", self.address)
        self.registerField("password1*", self.password1)
        self.registerField("password2*", self.password2)

    def validatePage(self):
        """ Test if passwords matching
            and password saving
        """
        # password matching ?
        if self.password2.text().compare(self.password1.text()):
            # password not matching
            error = QtGui.QMessageBox(QtGui.QMessageBox.Critical, "Password error", "Passwords don't match")
            error.exec_()
            return False
        # Empty password
        if not self.password2.text().compare(""):
            error = QtGui.QMessageBox(QtGui.QMessageBox.Critical, "Empty password", "Password can't be empty")
            error.exec_()
            return False
        # test to register account
        elif not registerAccount(unicode(self.username.text()), unicode(self.address.text()), unicode(self.password1.text())):
            return False
        # Reload config
        self.parent.parent.settings.sync()
        return True


class Page3(QtGui.QWizardPage):
    def __init__(self, parent=None):
        """ Final page
        """
        QtGui.QWizardPage.__init__(self, parent)
        self.parent = parent
        self.setTitle("Account activation successfully")
        label = QtGui.QLabel("You account is now activated. "
                            "You can now connect to the vault.\n"
                            "\n"
                            )
        label.setWordWrap(True)

        self.savepassword_label = QtGui.QLabel("Save your password in your wallet")
        self.savepassword = QtGui.QCheckBox()
        self.savepassword.setCheckState(QtCore.Qt.Checked)
        self.savepassword_label.setBuddy(self.savepassword)
        layout = QtGui.QGridLayout()
        layout.addWidget(label,0,0,1,2)
        layout.addWidget(self.savepassword_label,1,0)
        layout.addWidget(self.savepassword,1,1)
        self.setFinalPage(True)
        self.setLayout(layout)

    def validatePage(self):
        if self.savepassword.checkState() == QtCore.Qt.Checked:
            # Launch savepassword wizard
            self.savepass = SavePasswordWizard(self.field("password1").toString(), parent=self.parent.parent)
        return True
