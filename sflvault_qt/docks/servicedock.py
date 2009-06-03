#!/usr/bin/env python
# -*- coding: UTF-8 -*-

import sys
from PyQt4 import QtCore, QtGui
import re
from PyQt4.QtCore import Qt
import sflvault
from sflvault.client import SFLvaultClient
import shutil
import os


from auth import auth
token = auth.getAuth()


class ServiceInfoDock(QtGui.QDockWidget):
    def __init__(self, parent=None ):
        QtGui.QDockWidget.__init__(self, "Service", parent)
        self.parent = parent
        self.serviceInfo = ServiceInfo()
        self.setWidget(self.serviceInfo)
        global token

    def showInformations(self, id):
        """
            Show services informations
        """

        if id:
            service = token.vault.service.get(token.authtok,id)
            self.serviceInfo.url.setText(service["service"]["url"])
            self.serviceInfo.notes.setText(service["service"]["notes"])
            self.serviceInfo.servparent.setText(str(service["service"]["parent_service_id"]))
            self.serviceInfo.metadata.setText(str(service["service"]["metadata"]))
        else:
            self.serviceInfo.url.clear()
            self.serviceInfo.notes.clear()
            self.serviceInfo.servparent.clear()
            self.serviceInfo.metadata.clear()

    

class ServiceInfo(QtGui.QWidget):
    def __init__(self, parent=None ):
        QtGui.QWidget.__init__(self, parent)
        self.parent = parent

        # QlineEdits
        self.url = QtGui.QLineEdit()
        self.urlLabel = QtGui.QLabel(self.tr("Url"))
        self.notes = QtGui.QLineEdit()
        self.notesLabel = QtGui.QLabel(self.tr("Notes"))
        self.servparent = QtGui.QLineEdit()
        self.servparentLabel = QtGui.QLabel(self.tr("Service Parent"))
        self.metadata = QtGui.QLineEdit()
        self.metadataLabel = QtGui.QLabel(self.tr("Metadata"))
#        self.groupslist = QtGui.QLineEdit()

        # QGridLayout
        mainLayout = QtGui.QGridLayout()
        mainLayout.addWidget(self.urlLabel,0,0)
        mainLayout.addWidget(self.url,0,1)
        mainLayout.addWidget(self.notesLabel,1,0)
        mainLayout.addWidget(self.notes,1,1)
        mainLayout.addWidget(self.servparentLabel,2,0)
        mainLayout.addWidget(self.servparent,2,1)
        mainLayout.addWidget(self.metadataLabel,3,0)
        mainLayout.addWidget(self.metadata,3,1)

        # Geometries
        self.setWindowTitle(self.tr("Service Informations"))

        # Show window
        self.setLayout(mainLayout)

        
