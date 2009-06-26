# -*- coding: UTF-8 -*-

import sys
from PyQt4 import QtCore, QtGui
from sflvault.client import SFLvaultClient
from images.qicons import *
import socket
import xmlrpclib
import exceptions


class ErrorMessage(QtGui.QMessageBox):
    def __init__(self, exception, parent=None):
        QtGui.QMessageBox.__init__(self, parent)
        self.exception = exception
        if isinstance(self.exception, exceptions.ValueError):
            self.noPassword()
        elif isinstance(self.exception, socket.error):
            if self.exception[0] == 111:
                self.connectionError()
            elif self.exception[0] == -2:
                self.messageError()
        elif isinstance(self.exception, xmlrpclib.ProtocolError):
            # Protocol error means the token is now invalid
            self.protocolError()
        else:
            self.message()
        self.exec_()
        
    def messageError(self):
        self.setWindowTitle(self.tr("Message Error"))
        self.setText(self.exception[1].decode("utf8"))
        self.setIcon(QtGui.QMessageBox.Critical)

    def connectionError(self):
        self.setWindowTitle(self.tr("Connection Error"))
        self.setText(self.exception[1].decode("utf8"))
        self.setIcon(QtGui.QMessageBox.Critical)

    def protocolError(self):
        self.setWindowTitle(self.tr("Protocol Error"))
        #self.setText(self.exception.message))
        self.setText("Protocol")
        self.setIcon(QtGui.QMessageBox.Critical)

    def noPassword(self):
        self.setWindowTitle(self.tr("Environment Problem"))
        print self.exception
        self.setText(self.exception)
        self.setIcon(QtGui.QMessageBox.Critical)

    def message(self):
        if not self.exception:
            self.setWindowTitle(self.tr("Connection"))
            self.setText(self.exception)
        else:
            self.setWindowTitle(self.tr("Error"))
            self.setText(self.tr("Unknown error"))
        self.setIcon(QtGui.QMessageBox.Critical)
