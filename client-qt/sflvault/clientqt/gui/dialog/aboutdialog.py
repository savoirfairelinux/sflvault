#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
#    sflvault_qt/bar/filterbar.py
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
from sflvault.clientqt.images.qicons import *
import shutil
import os
import pkg_resources as pkgres
import webbrowser

class Help_dialog(QtWidgets.QDialog):
    def __init__(self, parent):
        QtWidgets.QDialog.__init__(self, parent)
        # title & message
        #from PyQt4 import QtCore
        #QtCore.pyqtRemoveInputHook()
        #import pdb; pdb.set_trace()
        self.setWindowTitle('SFLvault Help')
        distr = pkgres.get_distribution('SFLvault_client')

        self.msg1 = QtWidgets.QLabel(" SFLvault Help")
        self.msg2 = QtWidgets.QLabel(""" <a href="http://sflvault.org">http://sflvault.org</a> """)
        self.close_button = QtWidgets.QPushButton("Close")

        icon = Qicons("sflvault_icon")
        self.icon = QtWidgets.QLabel("")
        self.icon.setPixmap(icon.pixmap(64,64))
        # layout
        layout = QtWidgets.QGridLayout(self)
        layout.addWidget(self.icon, 0,0, 2, 1)
        layout.addWidget(self.msg1, 0,1,1,2)
        layout.addWidget(self.msg2, 1,1,1,2)
        layout.addWidget(self.close_button, 2,2)

        # windows properties
        self.setWindowModality(Qt.ApplicationModal)

        self.close_button.clicked.connect(self.close)
        self.msg2.linkActivated.connect(self.link)

    def link(self, link):
        webbrowser.open_new_tab(link)

    def close(self):
        self.accept()


class AboutDialog(QtWidgets.QDialog):
    def __init__(self, parent):
        QtWidgets.QDialog.__init__(self, parent)
        # title & message
        #from PyQt4 import QtCore
        #QtCore.pyqtRemoveInputHook()
        #import pdb; pdb.set_trace()
        self.setWindowTitle('About SFLvault')
        distr = pkgres.get_distribution('SFLvault_client')

        self.msg1 = QtWidgets.QLabel(" About SFLvault")
        self.msg2 = QtWidgets.QLabel(" " + 
                                 distr.project_name +
                                 " : " +
                                 distr.version)
        self.close_button = QtWidgets.QPushButton("Close")

        icon = Qicons("sflvault_icon")
        self.icon = QtWidgets.QLabel("")
        self.icon.setPixmap(icon.pixmap(64,64))
        # layout
        layout = QtWidgets.QGridLayout(self)
        layout.addWidget(self.icon, 0,0, 2, 1)
        layout.addWidget(self.msg1, 0,1,1,2)
        layout.addWidget(self.msg2, 1,1,1,2)
        layout.addWidget(self.close_button, 2,2)

        # windows properties
        self.setWindowModality(Qt.ApplicationModal)

        self.close_button.clicked.connect(self.close)

    def close(self):
        self.accept()


class About_sflvaultqt_dialog(QtWidgets.QDialog):
    def __init__(self, parent):
        QtWidgets.QDialog.__init__(self, parent)
        # title & message
        #from PyQt4 import QtCore
        #QtCore.pyqtRemoveInputHook()
        #import pdb; pdb.set_trace()
        self.setWindowTitle('About SFLvault Qt')
        distr = pkgres.get_distribution('SFLvault_client_qt')

        self.msg1 = QtWidgets.QLabel(" About SFLvault Qt")
        self.msg2 = QtWidgets.QLabel(" " +
                                 distr.project_name +
                                 " : " +
                                 distr.version)
        self.close_button = QtWidgets.QPushButton("Close")

        icon = Qicons("sflvault_icon")
        self.icon = QtWidgets.QLabel("")
        self.icon.setPixmap(icon.pixmap(64,64))
        # layout
        layout = QtWidgets.QGridLayout(self)
        layout.addWidget(self.icon, 0,0, 2, 1)
        layout.addWidget(self.msg1, 0,1,1,2)
        layout.addWidget(self.msg2, 1,1,1,2)
        layout.addWidget(self.close_button, 2,2)

        # windows properties
        self.setWindowModality(Qt.ApplicationModal)

        self.close_button.clicked.connect(self.close)


    def close(self):
        self.accept()

