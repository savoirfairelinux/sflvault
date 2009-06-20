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


class PreferencesWidget(QtGui.QDialog):
    def __init__(self, parent=None):
        QtGui.QDialog.__init__(self, parent)
        self.parent = parent
        self.settings = self.parent.settings

        # Load gui items
        self.save = QtGui.QPushButton(self.tr("Save"))
        self.cancel = QtGui.QPushButton(self.tr("Cancel"))

        self.usernameLabel = QtGui.QLabel(self.tr("User name :"))
        self.username = QtGui.QLineEdit()
        self.urlLabel = QtGui.QLabel(self.tr("Vault server address :"))
        self.url = QtGui.QLineEdit()
        self.saveMainWindowLabel = QtGui.QLabel(self.tr("Save dock positions :"))
        self.saveMainWindow = QtGui.QCheckBox()
        self.autoConnectLabel = QtGui.QLabel(self.tr("Auto connect :"))
        self.autoConnect = QtGui.QCheckBox()
        self.systrayLabel = QtGui.QLabel(self.tr("Show system tray :"))
        self.systray = QtGui.QCheckBox()
        self.effectsLabel = QtGui.QLabel(self.tr("Enabled effects :"))
        self.effects = QtGui.QCheckBox()
        self.filterLabel = QtGui.QLabel(self.tr("Filter bar :"))
        self.filter = QtGui.QCheckBox()

        # Vault Group Box
        vaultbox = QtGui.QGroupBox(self.tr("SFLvault preferences"))
        gridLayout = QtGui.QGridLayout()
        gridLayout.addWidget(self.usernameLabel,0,0)
        gridLayout.addWidget(self.username,0,1)
        gridLayout.addWidget(self.urlLabel,1,0)
        gridLayout.addWidget(self.url,1,1)
        vaultbox.setLayout(gridLayout)

        # Gui Group box
        guibox = QtGui.QGroupBox(self.tr("GUI preferences"))
        gridLayout = QtGui.QGridLayout()
        gridLayout.addWidget(self.saveMainWindowLabel,0,0)
        gridLayout.addWidget(self.saveMainWindow,0,1)
        gridLayout.addWidget(self.autoConnectLabel,1,0)
        gridLayout.addWidget(self.autoConnect,1,1)
        gridLayout.addWidget(self.systrayLabel,2,0)
        gridLayout.addWidget(self.systray,2,1)
        gridLayout.addWidget(self.effectsLabel,3,0)
        gridLayout.addWidget(self.effects,3,1)
        gridLayout.addWidget(self.filterLabel,4,0)
        gridLayout.addWidget(self.filter,4,1)
        guibox.setLayout(gridLayout)

        # Positionning items
        buttonLayout = QtGui.QHBoxLayout()
        buttonLayout.addStretch(1)
        buttonLayout.addWidget(self.save)
        buttonLayout.addWidget(self.cancel)

        mainLayout = QtGui.QVBoxLayout()
        mainLayout.addWidget(vaultbox)
        mainLayout.addWidget(guibox)
        mainLayout.addLayout(buttonLayout)
        self.setLayout(mainLayout)

        self.setWindowTitle(self.tr("Preferences"))

        # SIGNALS
        QtCore.QObject.connect(self.save, QtCore.SIGNAL("clicked()"), self.saveConfig)
        QtCore.QObject.connect(self.cancel, QtCore.SIGNAL("clicked()"), self, QtCore.SLOT("reject()"))

    def exec_(self):
        # load config
        self.readConfig()
        # Show dialog
        self.show()

    def readConfig(self):
        """
            ReadConfig
        """
        self.username.setText(self.settings.value("SFLvault/username").toString())
        self.url.setText(self.settings.value("SFLvault/url").toString())
        self.saveMainWindow.setCheckState(self.settings.value("SFLvault-qt4/savewindow").toInt()[0])
        self.autoConnect.setCheckState(self.settings.value("SFLvault-qt4/autoconnect").toInt()[0])
        self.systray.setCheckState(self.settings.value("SFLvault-qt4/systray").toInt()[0])
        self.effects.setCheckState(self.settings.value("SFLvault-qt4/effects").toInt()[0])
        self.filter.setCheckState(self.settings.value("SFLvault-qt4/filter").toInt()[0])

    def saveConfig(self):
        """
            Save configuration
        """
        self.settings.setValue("SFLvault/username", QtCore.QVariant(self.username.text()))
        self.settings.setValue("SFLvault/url", QtCore.QVariant(self.url.text()))
        self.settings.setValue("SFLvault-qt4/savewindow", QtCore.QVariant(self.saveMainWindow.checkState()))
        self.settings.setValue("SFLvault-qt4/autoconnect", QtCore.QVariant(self.autoConnect.checkState()))
        self.settings.setValue("SFLvault-qt4/effects", QtCore.QVariant(self.effects.checkState()))
        self.settings.setValue("SFLvault-qt4/filter", QtCore.QVariant(self.filter.checkState()))
        self.parent.loadUnloadSystray()
        self.parent.disEnableEffects()
        self.parent.showHideFilterBar()
        # Close dialog
        self.accept()

