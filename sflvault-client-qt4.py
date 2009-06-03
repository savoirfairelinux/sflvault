#!/usr/bin/env python
# -*- coding: UTF-8 -*-
    
from PyQt4 import QtCore, QtGui
from sflvault_qt import mainWindow
import sys
 
from auth import auth


if __name__ == "__main__":
    app = QtGui.QApplication(sys.argv)
  
    translator = QtCore.QTranslator()
    translator.load("frdfhvgjgg", "./dlb_translations")
    app.installTranslator(translator)
 
    mainwindow = mainWindow.MainWindow()
    mainwindow.show()
    sys.exit(app.exec_())
