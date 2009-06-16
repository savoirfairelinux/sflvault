# -*- coding: UTF-8 -*-

import sys
from PyQt4 import QtCore, QtGui
from sflvault.client import SFLvaultClient
from images.qicons import *


class ErrorMessage(QtGui.QMessageBox):
    def __init__(self, exception, parent=None):
        QtGui.QMessageBox.__init__(self, parent)
        print exception
        self.exception = exception
        if type(self.exception) == type([]): 
            if self.exception[0] == 111:
                self.connectionError()
                self.message()
        else:
            self.message()
        self.exec_()
        

    def connectionError(self):
        self.setWindowTitle(self.tr("Connection Error"))
        self.setText(self.tr(self.exception[1]))
        self.setIcon(QtGui.QMessageBox.Critical)

    def message(self):
        self.setWindowTitle(self.tr("Connection"))
        self.setText(self.exception)
        self.setIcon(QtGui.QMessageBox.Critical)
