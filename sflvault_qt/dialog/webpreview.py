#!/usr/bin/env python
# -*- coding: UTF-8 -*-
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
from PyQt4 import QtCore, QtGui, QtWebKit
import re
from PyQt4.QtCore import Qt
import sflvault
from sflvault.client import SFLvaultClient
from images.qicons import *
import shutil
import os


class WebPreview(QtGui.QWidget):
    def __init__(self, url, parent=None):
        QtGui.QWidget.__init__(self, parent)
#        self._boundingRect = QtCore.QRect(0, 0, 400, 300)

        self.setWindowFlags(QtCore.Qt.SplashScreen)

        self.webpreview = QtWebKit.QWebView()
        self.webpreview.load(url)
        self.webpreview.resize(200,200)


        self.resize(200,200)
        layout = QtGui.QVBoxLayout(self)
#        layout.addWidget(self.webpreview)


        self.proxyitem = QtGui.QGraphicsProxyWidget()
        self.proxyitem.setWidget(self.webpreview)
        
        layout.addWidget(self.proxyitem)
#        self.setAcceptHoverEvents(False)
        
#        xScale = (self._boundingRect.width() - 2 * frameWidth) / self.webpreview.width()
#        yScale = (self._boundingRect.height() - 2 * frameWidth) / self.webpreview.height()
#        print (xScale, yScale)
#        self.scale(xScale, yScale)
#        self.setPos(frameWidth, frameWidth)


#        scene = QtGui.QGraphicsScene()
#        scene.addWidget(self.webpreview)
#        scene.addText("Hello, world!")
#        view = QtGui.QGraphicsView(scene)
#        view.scale(xScale, yScale)
#        self.setScene(scene)       
#        view.show()

#        self.setZValue(300)

#    def paint(self, painter, option, widget): 
        #Q_UNUSED(option); Q_UNUSED(widget);
#        painter.setClipRect(self.boundingRect)
#        painter.setPen(QtCore.QPen(QtCore.Qt.black, 5))
#        painter.setBrush(QtCore.Qt.black);
#        painter.setRenderHints(QtCore.QPainter.Antialiasing);
#        painter.drawRoundedRect(self.boundingRect, 10, 10);
