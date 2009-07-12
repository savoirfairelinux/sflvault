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
        elif exception.message == "Unable to decrypt groupkey (Error decrypting: inconsistent message)":
            self.AccessError()
        else:
            self.message()
        print "qhow"
        self.exec_()
        
    def messageError(self):
        self.setWindowTitle(self.tr("Message Error"))
        self.setText(self.exception[1].decode("utf8"))
        print "message error"
        self.setIcon(QtGui.QMessageBox.Critical)

    def connectionError(self):
        self.setWindowTitle(self.tr("Connection Error"))
        self.setText(self.exception[1].decode("utf8"))
        print "connection error"
        self.setIcon(QtGui.QMessageBox.Critical)

    def AccessError(self):
        self.setWindowTitle(self.tr("Access Error"))
        self.setText("Access Denied")
        print "protocol error"
        self.setIcon(QtGui.QMessageBox.Critical)

    def protocolError(self):
        self.setWindowTitle(self.tr("Protocol Error"))
        self.setText("Protocol")
        print "protocol error"
        self.setIcon(QtGui.QMessageBox.Critical)

    def noPassword(self):
        self.setWindowTitle(self.tr("Environment Problem"))
        print self.exception
        print "no password"
        self.setText(self.exception)
        self.setIcon(QtGui.QMessageBox.Critical)

    def message(self):
        if self.exception:
            self.setWindowTitle(self.tr("Connection"))
            print "message connection"
            self.setText(self.exception.message)
        else:
            self.setWindowTitle(self.tr("Error"))
            self.setText(self.tr("Unknown error"))
            print "message unknown"
        self.setIcon(QtGui.QMessageBox.Critical)
