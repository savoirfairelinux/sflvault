#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
#    sflvault-client-qt4.py 
#
#    This file is part of SFLvault-QT
#
#    Copyright (C) 2014 Savoir-faire Linux inc.
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

    
from PyQt4 import QtCore, QtGui
from sflvault.clientqt.gui import mainWindow
import sys
from sflvault.clientqt.images.qicons import *
from sflvault.clientqt.lib.auth import *

## TODO USELESS ???
#import os
#os.environ['SFLVAULT_CONFIG'] = "~/Application Data/SFLvault/config2.ini"


def main():
    app = QtGui.QApplication(sys.argv)
  
    app.setWindowIcon(Qicons("sflvault_icon"))
 
    mainwindow = mainWindow.MainWindow(app)
    mainwindow.exec_()
    sys.exit(app.exec_())
