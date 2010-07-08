#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
#    sflvault_qt/bar/filterbar.py
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
from PyQt4 import QtCore, QtGui
import re
from PyQt4.QtCore import Qt
import sflvault
from sflvault.client import SFLvaultClient
from sflvault.clientqt.images.qicons import *
import shutil
import os


class ProgressDialog(QtGui.QDialog):
    def __init__(self, title, message, function, *args):
        QtGui.QDialog.__init__(self, None)
        self.function = function
        self.args = args

        # title & message
        self.setWindowTitle(title)
        self.message = QtGui.QLabel(message)
        # layout
        layout = QtGui.QVBoxLayout(self)
        layout.addWidget(self.message)
        self.progress = QtGui.QProgressBar()
        self.progress.setMinimum(0)
        self.progress.setMaximum(0)
        layout.addWidget(self.progress)

        # windows properties
        self.setWindowModality(Qt.ApplicationModal)


        class Thread(QtCore.QThread):
            def __init__(self, parent, function, *args):
                QtCore.QThread.__init__(self, parent)
                self.function = function
            
            def run(self):
                # Launch function
                ret = self.function(*args)
                self.quit()
    
        # Create thread
        self.thread = Thread(self, self.function, self.args)

        QtCore.QObject.connect(self.thread, QtCore.SIGNAL("finished()"), self.close)

    def run(self):
        # launch thread
        self.thread.start() 
        # launch dialog
        return self.exec_()

    def closeEvent(self, event):
        """
            Ignore close event for progressdialog
        """ 
        event.ignore()

    def close(self):
        self.accept()
