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
from sflvault.clientqt.images.qicons import *
import shutil
import os


class FilterBar(QtGui.QWidget):
    def __init__(self, parent=None):
        QtGui.QWidget.__init__(self, parent)
        self.parent = parent

        layout = QtGui.QHBoxLayout(self)
        layout.setMargin(0)

        self.close = QtGui.QToolButton(self);
        self.close.setAutoRaise(True)
        self.close.setIcon(Qicons("close"))
        self.close.setToolTip(self.tr("Hide Filter Bar"))
        layout.addWidget(self.close)

        self.filter_label = QtGui.QLabel(self.tr("Filter : "))
        layout.addWidget(self.filter_label)

        self.filter_input = QtGui.QLineEdit(self)
        self.filter_input.setLayoutDirection(QtCore.Qt.LeftToRight)
        self.filter_label.setBuddy(self.filter_input)
        layout.addWidget(self.filter_input)

        QtCore.QObject.connect(self.close, QtCore.SIGNAL("clicked()"), self.hide)
