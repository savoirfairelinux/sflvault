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
from PyQt4 import QtCore, QtGui
import re
from PyQt4.QtCore import Qt
import sflvault
from sflvault.client import SFLvaultClient
from sflvault.clientqt.images.qicons import *
import shutil
import os
import pkg_resources as pkgres
import webbrowser

class Help_dialog(QtGui.QDialog):
    def __init__(self, parent):
        QtGui.QDialog.__init__(self, parent)
        # title & message
        #from PyQt4 import QtCore
        #QtCore.pyqtRemoveInputHook()
        #import pdb; pdb.set_trace()
        self.setWindowTitle('SFLvault Help')
        distr = pkgres.get_distribution('SFLvault_client')

        self.msg1 = QtGui.QLabel(" SFLvault Help")
        self.msg2 = QtGui.QLabel(""" <a href="http://sflvault.org">http://sflvault.org</a> """)
        self.close_button = QtGui.QPushButton("Close")

        icon = Qicons("sflvault_icon")
        self.icon = QtGui.QLabel("")
        self.icon.setPixmap(icon.pixmap(64,64))
        # layout
        layout = QtGui.QGridLayout(self)
        layout.addWidget(self.icon, 0,0, 2, 1)
        layout.addWidget(self.msg1, 0,1,1,2)
        layout.addWidget(self.msg2, 1,1,1,2)
        layout.addWidget(self.close_button, 2,2)

        # windows properties
        self.setWindowModality(Qt.ApplicationModal)

        QtCore.QObject.connect(self.close_button, QtCore.SIGNAL("clicked()"), self.close)
        QtCore.QObject.connect(self.msg2, QtCore.SIGNAL("linkActivated (const QString&)"), self.link)

    def link(self, link):
        webbrowser.open_new_tab(link)

    def close(self):
        self.accept()


class AboutDialog(QtGui.QDialog):
    def __init__(self, parent):
        QtGui.QDialog.__init__(self, parent)
        # title & message
        #from PyQt4 import QtCore
        #QtCore.pyqtRemoveInputHook()
        #import pdb; pdb.set_trace()
        self.setWindowTitle('About SFLvault')
        distr = pkgres.get_distribution('SFLvault_client')

        self.msg1 = QtGui.QLabel(" About SFLvault")
        self.msg2 = QtGui.QLabel(" " + 
                                 distr.project_name +
                                 " : " +
                                 distr.version)
        self.close_button = QtGui.QPushButton("Close")

        icon = Qicons("sflvault_icon")
        self.icon = QtGui.QLabel("")
        self.icon.setPixmap(icon.pixmap(64,64))
        # layout
        layout = QtGui.QGridLayout(self)
        layout.addWidget(self.icon, 0,0, 2, 1)
        layout.addWidget(self.msg1, 0,1,1,2)
        layout.addWidget(self.msg2, 1,1,1,2)
        layout.addWidget(self.close_button, 2,2)

        # windows properties
        self.setWindowModality(Qt.ApplicationModal)

        QtCore.QObject.connect(self.close_button, QtCore.SIGNAL("clicked()"), self.close)

    def close(self):
        self.accept()


class About_sflvaultqt_dialog(QtGui.QDialog):
    def __init__(self, parent):
        QtGui.QDialog.__init__(self, parent)
        # title & message
        #from PyQt4 import QtCore
        #QtCore.pyqtRemoveInputHook()
        #import pdb; pdb.set_trace()
        self.setWindowTitle('About SFLvault Qt')
        distr = pkgres.get_distribution('SFLvault_client_qt')

        self.msg1 = QtGui.QLabel(" About SFLvault Qt")
        self.msg2 = QtGui.QLabel(" " +
                                 distr.project_name +
                                 " : " +
                                 distr.version)
        self.close_button = QtGui.QPushButton("Close")

        icon = Qicons("sflvault_icon")
        self.icon = QtGui.QLabel("")
        self.icon.setPixmap(icon.pixmap(64,64))
        # layout
        layout = QtGui.QGridLayout(self)
        layout.addWidget(self.icon, 0,0, 2, 1)
        layout.addWidget(self.msg1, 0,1,1,2)
        layout.addWidget(self.msg2, 1,1,1,2)
        layout.addWidget(self.close_button, 2,2)

        # windows properties
        self.setWindowModality(Qt.ApplicationModal)

        QtCore.QObject.connect(self.close_button, QtCore.SIGNAL("clicked()"), self.close)


    def close(self):
        self.accept()

