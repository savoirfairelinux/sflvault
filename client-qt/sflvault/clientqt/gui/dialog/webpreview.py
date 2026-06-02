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
from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtWebEngineWidgets import QWebEngineView as QWebView
import re
from PyQt5.QtCore import Qt
import sflvault
from sflvault.client import SFLvaultClient
from sflvault.clientqt.images.qicons import *
import shutil
import os


class WebPreviewWidget(QtWidgets.QWidget):
    def __init__(self, parent=None):
        """ Widget to show a preview
            of web site
        """
        QtWidgets.QWidget.__init__(self, parent)
    
        # Widget options
        self.setAttribute(QtCore.Qt.WA_DeleteOnClose, False)
        # Define widget as tooltip !!!
        self.setWindowFlags(QtCore.Qt.ToolTip)

        # Prepare webpreview 
        self.webpreview = WebPreview(self)

        # Layout
        layout = QtWidgets.QVBoxLayout(self)
        # Load proxy widget 
        self.proxyitem = QtWidgets.QGraphicsProxyWidget()
        self.proxyitem.setWidget(self.webpreview)
        # Scence
        scene = QtWidgets.QGraphicsScene()
        scene.addItem(self.proxyitem)
        # View
        view = QtWidgets.QGraphicsView(scene)
        ## rescale view
        view.scale(0.4, 0.4)
        view.setScene(scene)

        # Add view to widget
        layout.addWidget(view)

    def mousePressEvent(self, event):
        """Enable move widget
        """
        self.close()

class WebPreview(QWebView):
    def __init__(self, parent=None):
        """
        """
        QWebView.__init__(self, None)
        self.parent = parent

    def mousePressEvent(self, event):
        """Enable move widget
        """
        self.parent.close()
