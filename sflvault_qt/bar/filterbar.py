#!/usr/bin/env python
# -*- coding: UTF-8 -*-

import sys
from PyQt4 import QtCore, QtGui
import re
from PyQt4.QtCore import Qt
import sflvault
from sflvault.client import SFLvaultClient
from images.qicons import *
import shutil
import os


class FilterBar(QtGui.QWidget):
    def __init__(self, parent=None):
        QtGui.QWidget.__init__(self, parent)
        self.parent = parent

        layout = QtGui.QHBoxLayout(self)
        layout.setMargin(0)

        self.close = QtGui.QToolButton(self);
        self.close.setAutoRaise(True);
        self.close.setIcon(Qicons("close"))
        self.close.setToolTip(self.tr("Hide Filter Bar"))
        layout.addWidget(self.close);

        self.filter_label = QtGui.QLabel(self.tr("Filter : "));
        layout.addWidget(self.filter_label);

        self.filter_input = QtGui.QLineEdit(self)
        self.filter_input.setLayoutDirection(QtCore.Qt.LeftToRight)
        self.filter_label.setBuddy(self.filter_input);
        layout.addWidget(self.filter_input);

        QtCore.QObject.connect(self.close, QtCore.SIGNAL("clicked()"), self.hide)
