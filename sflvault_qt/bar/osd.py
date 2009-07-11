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
from images.qicons import *
from lib.auth import *


class Osd(QtGui.QWidget):
    def __init__(self, password=None, address=None, username=None, parent=None, ):
        QtGui.QSystemTrayIcon.__init__(self, parent)
        self.parent = parent
        # Define widget as a tooltip
        self.setWindowFlags(QtCore.Qt.ToolTip) 

        # QGridLayout
        mainLayout = QtGui.QGridLayout()

        # Define labels, buttons and add to grid if necessary
        if username:
            self.userLabel = QtGui.QLabel(self.tr("User name : "))
            self.user = QtGui.QLabel(username)
            self.user.setTextInteractionFlags(QtCore.Qt.TextBrowserInteraction)
            self.userCopy = QtGui.QPushButton(self.tr("Copy"))
            mainLayout.addWidget(self.userLabel,0,0)
            mainLayout.addWidget(self.user,0,1)
            mainLayout.addWidget(self.userCopy,0,2)
        if address:
            self.addressLabel = QtGui.QLabel(self.tr("Address : "))
            self.address = QtGui.QLabel(address)
            self.address.setTextInteractionFlags(QtCore.Qt.TextBrowserInteraction)
            self.addressCopy = QtGui.QPushButton(self.tr("Copy"))
            mainLayout.addWidget(self.addressLabel,1,0)
            mainLayout.addWidget(self.address,1,1)
            mainLayout.addWidget(self.addressCopy,1,2)
        if password:
            self.passwordLabel = QtGui.QLabel(self.tr("Password : "))
            self.password = QtGui.QLabel(password)
            self.password.setTextInteractionFlags(QtCore.Qt.TextBrowserInteraction)
            self.passwordCopy = QtGui.QPushButton(self.tr("Copy"))
            mainLayout.addWidget(self.passwordLabel,2,0)
            mainLayout.addWidget(self.password,2,1)
            mainLayout.addWidget(self.passwordCopy,2,2)
        # Define close button
        self.closeButton = QtGui.QPushButton(self.tr("&Close"))
        mainLayout.addWidget(self.closeButton,3,0,1,3)

        # Geometries
        self.setWindowTitle(self.tr("Informations"))

        # Show window
        self.setLayout(mainLayout)

        # Load old position
        if self.parent.settings.value("osd/posx").isValid():
            posx, bool = self.parent.settings.value("osd/posx").toInt()
            posy, bool = self.parent.settings.value("osd/posy").toInt()
            self.setGeometry(posx,posy,1,1)

        # Signals
        ## Close widhet
        QtCore.QObject.connect(self.closeButton, QtCore.SIGNAL("clicked()"), self.close)
        ## Copy user to clipboard
        QtCore.QObject.connect(self.userCopy, QtCore.SIGNAL("clicked()"), self.copyUser)
        ## Copy address to clipboard
        QtCore.QObject.connect(self.addressCopy, QtCore.SIGNAL("clicked()"), self.copyAddress)
        ## Copy password to clipboard
        QtCore.QObject.connect(self.passwordCopy, QtCore.SIGNAL("clicked()"), self.copyPassword)


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
            self.parent.settings.setValue("osd/posx", QtCore.QVariant(posx))
            self.parent.settings.setValue("osd/posy", QtCore.QVariant(posy))

    def copyUser(self):
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
