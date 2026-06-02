#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
#    sflvault_qt/bar/ocd.py
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
from sflvault.clientqt.images.qicons import *
from sflvault.clientqt.lib.auth import *


class Osd(QtWidgets.QWidget):
    def __init__(self, password=None, address=None, username=None, parent=None, ):
        QtWidgets.QWidget.__init__(self, parent)
        self.parent = parent
        # Define widget as a tooltip
        self.setWindowFlags(QtCore.Qt.ToolTip) 

        # QGridLayout
        mainLayout = QtWidgets.QGridLayout()

        # Define labels, buttons and add to grid if necessary
        if username:
            self.usernameLabel = QtWidgets.QLabel(self.tr("User name : "))
            self.username = QtWidgets.QLineEdit(username)
            self.username.setReadOnly(True)
            self.usernameCopy = QtWidgets.QPushButton(self.tr("Copy"))
            mainLayout.addWidget(self.usernameLabel,0,0)
            mainLayout.addWidget(self.username,0,1)
            mainLayout.addWidget(self.usernameCopy,0,2)
        if address:
            self.addressLabel = QtWidgets.QLabel(self.tr("Address : "))
            self.address = QtWidgets.QLineEdit(address)
            self.address.setReadOnly(True)
            self.addressCopy = QtWidgets.QPushButton(self.tr("Copy"))
            mainLayout.addWidget(self.addressLabel,1,0)
            mainLayout.addWidget(self.address,1,1)
            mainLayout.addWidget(self.addressCopy,1,2)
        if password:
            self.passwordLabel = QtWidgets.QLabel(self.tr("Password : "))
            self.password = QtWidgets.QLineEdit(password)
            self.password.setReadOnly(True)
#            self.password.setTextInteractionFlags(QtCore.Qt.TextBrowserInteraction)
            self.passwordCopy = QtWidgets.QPushButton(self.tr("Copy"))
            mainLayout.addWidget(self.passwordLabel,2,0)
            mainLayout.addWidget(self.password,2,1)
            mainLayout.addWidget(self.passwordCopy,2,2)
        # Define close button
        self.closeButton = QtWidgets.QPushButton(self.tr("&Close"))
        mainLayout.addWidget(self.closeButton,3,0,1,3)

        # Geometries
        self.setWindowTitle(self.tr("Informations"))

        # Show window
        self.setLayout(mainLayout)

        # Load old position
        if self.parent.settings.value("osd/posx") is not None:
            # get current width
            width = self.geometry().getCoords()[3]
            # get saved position
            posx = int(self.parent.settings.value("osd/posx", 0))
            posy = int(self.parent.settings.value("osd/posy", 0))
            self.setGeometry(posx, posy, width, 1) 

        # FIXME
        # Ajust Size
        if password:
            self.password.adjustSize()
        if username:
            self.username.adjustSize()
        if address:
            self.address.adjustSize()
        # Set maximum size
        self.setMaximumWidth(700)
        self.setMinimumWidth(300)
        ## END MEFIX

        # Signals
        ## Close widhet
        self.closeButton.clicked.connect(self.close)
        if username:
            ## Copy user to clipboard
            self.usernameCopy.clicked.connect(self.copyUsername)
        if address:
            ## Copy address to clipboard
            self.addressCopy.clicked.connect(self.copyAddress)
        if password:
            ## Copy password to clipboard
            self.passwordCopy.clicked.connect(self.copyPassword)

        # Check if timer is set
        timerTimeout = int(self.parent.settings.value("osd/timer", 0))
        if timerTimeout > 0:
            # If yes launch timer 
            self.timer = QtCore.QTimer(self)
            self.timer.start(timerTimeout * 1000)
            # Connect timeout timer with widget close function
            self.timer.timeout.connect(self.close)

    def mousePressEvent(self, event):
        """
            Enable move widget
        """
        if event.button() == QtCore.Qt.LeftButton:
            self.dragPosition = event.globalPos() - self.frameGeometry().topLeft()
            event.accept()

    def mouseMoveEvent(self, event):
        """
            Enable move widget
        """
        if event.buttons() == QtCore.Qt.LeftButton:
            self.move(event.globalPos() - self.dragPosition)
            event.accept()
            # Save new position
            posx, posy, width, heigth = self.geometry().getCoords()
            self.parent.settings.setValue("osd/posx", posx)
            self.parent.settings.setValue("osd/posy", posy)

    def copyUsername(self):
        """
            Copy user to clipboard
        """
        self.parent.copyToClip(self.user.text()) 

    def copyAddress(self):
        """
            Copy address to clipboard
        """
        self.parent.copyToClip(self.address.text()) 

    def copyPassword(self):
        """
            Copy password to clipboard
        """
        self.parent.copyToClip(self.password.text())
