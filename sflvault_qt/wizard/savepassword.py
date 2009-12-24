#!/usr/bin/env python
# -*- coding: UTF-8 -*-
#
#    sflvault_qt/wizard/savepassword.py
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

PAGE_INTRO = 0
PAGE_PASSWORD = 1
PAGE_SUCCESS = 2
PAGE_UNSUCCESS = 3

class SavePasswordWizard(QtGui.QWizard):
    def __init__(self, parent=None):
        QtGui.QWizard.__init__(self, parent)
        self.parent = parent

        self.setPage(PAGE_INTRO, Page1())
        self.setPage(PAGE_PASSWORD, Page2())
        self.setPage(PAGE_SUCCESS, Page3())
        self.setPage(PAGE_UNSUCCESS, Page4())

        self.setWindowTitle("Save your password")
        self.show()


class Page1(QtGui.QWizardPage):
    def __init__(self, parent=None):
        QtGui.QWizard.__init__(self, parent)
        self.parent = parent

        self.setTitle("Account Activation")

        label = QtGui.QLabel()
        label.setWordWrap(True)

        layout = QtGui.QVBoxLayout()
        layout.addWidget(label)
        self.setLayout(layout)

        if not "KDE_SESSION_VERSION" in os.environ or not os.environ["KDE_SESSION_VERSION"] == "4":
            label.setText("Your system doesn't have a supported wallet."
                        )
            self.next_page = PAGE_UNSUCCESS
        else:
            label.setText("This wizard will activate your account."
                        )
            self.next_page = PAGE_PASSWORD

    def nextId(self):
        return self.next_page


class Page2(QtGui.QWizardPage):
    def __init__(self, parent=None):
        QtGui.QWizardPage.__init__(self, parent)
        self.parent = parent
        self.setTitle("Initialize your vault account")
        self.setSubTitle("Fill this form")
        self.setCommitPage(True)
        self.next_page = PAGE_SUCCESS

        password1_label = QtGui.QLabel(self.tr("&Password"))
        self.password1 = QtGui.QLineEdit()
        self.password1.setEchoMode(QtGui.QLineEdit.Password)
        password1_label.setBuddy(self.password1)

        password2_label = QtGui.QLabel(self.tr("Confirm your password"))
        self.password2 = QtGui.QLineEdit()
        self.password2.setEchoMode(QtGui.QLineEdit.Password)
        password2_label.setBuddy(self.password2)

        layout = QtGui.QGridLayout(self)
        layout.addWidget(password1_label,0,0)
        layout.addWidget(self.password1,0,1)
        layout.addWidget(password2_label,1,0)
        layout.addWidget(self.password2,1,1)

        self.setLayout(layout)
        self.registerField("password1*", self.password1)
        self.registerField("password2*", self.password2)

    def validatePage(self):
        if self.password2.text().compare(self.password1.text()):
            error = QtGui.QMessageBox(QtGui.QMessageBox.Critical, "Password error", "Passwords don't match")
            error.exec_()
            return False
        
        if not "KDE_SESSION_VERSION" in os.environ or not os.environ["KDE_SESSION_VERSION"] == "4":
            ret = KDEsavePassword(self.password1.text())
            if ret:
                self.next_page = PAGE_SUCCESS
            else:
                self.next_page = PAGE_UNSUCCESS
        else:
            print "error ???"
        return True

    def nextId(self):
        return self.next_page


class Page3(QtGui.QWizardPage):
    def __init__(self, parent=None):
        QtGui.QWizardPage.__init__(self, parent)
        self.parent = parent

        self.setTitle("Password saved successfully")

        label = QtGui.QLabel("Your password was saved in your wallet."
                            )
        label.setWordWrap(True)

        layout = QtGui.QVBoxLayout()
        layout.addWidget(label)
        self.setFinalPage(True)
        self.setLayout(layout)

    def nextId(self):
        return -1


class Page4(QtGui.QWizardPage):
    def __init__(self, parent=None):
        QtGui.QWizardPage.__init__(self, parent)
        self.parent = parent

        self.setTitle("Password saved unsuccessfully")

        label = QtGui.QLabel("Your password was NOT saved in your wallet."
                            )
        label.setWordWrap(True)

        layout = QtGui.QVBoxLayout()
        layout.addWidget(label)
        self.setFinalPage(True)
        self.setLayout(layout)

    def nextId(self):
        return -1
