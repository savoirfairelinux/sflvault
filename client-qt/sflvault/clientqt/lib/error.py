#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
#    lib/error.py
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
from sflvault.client import SFLvaultClient
from sflvault.clientqt.images.qicons import *
import socket
import xmlrpc.client as xmlrpclib


class ErrorMessage(QtWidgets.QMessageBox):
    def __init__(self, exception, parent=None):
        QtWidgets.QMessageBox.__init__(self, parent)
        self.exception = exception
        if isinstance(self.exception, ValueError):
            self.noPassword()
        elif isinstance(self.exception, socket.error):
            if self.exception[0] == 111:
                self.connectionError()
            elif self.exception[0] == -2:
                self.message()
            elif self.exception[0] == 4:
                # Error : (4, 'Appel syst\xc3\xa8me interrompu')
                # Call xmlrpm interumpted
                # Do nothing
                return None
            elif self.exception[0] == 133:
                # Error : (113, "Aucun chemin d'acc\xc3\xa8s pour atteindre l'h\xc3\xb4te cible")
                self.connectionError()
            elif self.exception[0] == 1:
                # SSL ERROR
                self.protocolError()
        elif isinstance(self.exception, xmlrpclib.ProtocolError):
            # Protocol error means the token is now invalid
            self.protocolError()
        elif getattr(exception, 'message', ''):
            if exception.message == "Unable to decrypt groupkey (Error decrypting: inconsistent message)":
                self.AccessError()
            else:
                self.message() 
        else:
            self.message()
        self.exec_()
        
    def messageError(self):
        self.setWindowTitle(self.tr("Message Error"))
        self.setText(str(self.exception.args[1]) if len(self.exception.args) > 1 else str(self.exception))
        print("message error")
        self.setIcon(QtWidgets.QMessageBox.Critical)

    def connectionError(self):
        self.setWindowTitle(self.tr("Connection Error"))
        self.setText(str(self.exception.args[1]) if len(self.exception.args) > 1 else str(self.exception))
        print("connection error")
        self.setIcon(QtWidgets.QMessageBox.Critical)

    def AccessError(self):
        self.setWindowTitle(self.tr("Access Error"))
        self.setText("Access Denied")
        print("access denied")
        self.setIcon(QtWidgets.QMessageBox.Critical)

    def protocolError(self):
        self.setWindowTitle(self.tr("Protocol Error"))
        self.setText("Protocol Error")
        print("protocol error")
        self.setIcon(QtWidgets.QMessageBox.Critical)

    def noPassword(self):
        self.setWindowTitle(self.tr("Environment Problem"))
        print("no password")
        self.setText("No password Found")
        self.setIcon(QtWidgets.QMessageBox.Critical)

    def message(self):
        if isinstance(self.exception, str):
            self.setWindowTitle(self.tr("Error message"))
            self.setText(self.exception)
        elif self.exception and hasattr(self.exception, 'message'):
            self.setWindowTitle(self.tr("Error message"))
            self.setText(getattr(self.exception, "message", str(self.exception)))
        elif self.exception:
            print("message error")
            try:
                self.setWindowTitle(self.tr("Error message"))
                self.setText(self.exception[1])
            except IndexError as e:
                self.setWindowTitle(self.tr("Error Message"))
                self.setText(getattr(self.exception, "message", str(self.exception)))
        else:
            self.setWindowTitle(self.tr("Error"))
            self.setText(self.tr("Unknown error"))
            print("message unknown")
        self.setIcon(QtWidgets.QMessageBox.Critical)
