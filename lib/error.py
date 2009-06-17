# -*- coding: UTF-8 -*-

import sys
from PyQt4 import QtCore, QtGui
from sflvault.client import SFLvaultClient
from images.qicons import *
import socket


class ErrorMessage(QtGui.QMessageBox):
    def __init__(self, exception, parent=None):
        QtGui.QMessageBox.__init__(self, parent)
        self.exception = exception
        if isinstance(self.exception, socket.error):
            if self.exception[0] == 111:
                self.connectionError()
        else:
            self.message()
        self.exec_()
        

    def connectionError(self):
        self.setWindowTitle(self.tr("Connection Error"))
        self.setText(self.exception[1].decode("utf8"))
        self.setIcon(QtGui.QMessageBox.Critical)

    def message(self):
        self.setWindowTitle(self.tr("Connection"))
        print self.exception
        print type(self.exception)
        self.setText(self.exception)
        self.setIcon(QtGui.QMessageBox.Critical)
