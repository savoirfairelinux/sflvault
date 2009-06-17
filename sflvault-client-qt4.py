#!/usr/bin/env python
# -*- coding: UTF-8 -*-
    
from PyQt4 import QtCore, QtGui
from sflvault_qt import mainWindow
import sys
from images.qicons import *
from lib.auth import *


if __name__ == "__main__":
    app = QtGui.QApplication(sys.argv)
  
    translator = QtCore.QTranslator()
    translator.load("frdfhvgjgg", "./dlb_translations")
    app.installTranslator(translator)

    app.setWindowIcon(Qicons("sflvault_icon"))
 
    mainwindow = mainWindow.MainWindow()
#    mainwindow.show()
    mainwindow.exec_()
    sys.exit(app.exec_())
