#!/usr/bin/env python
# -*- coding: UTF-8 -*-
#
#    sflvault_qt/config/preferences.py
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
import re
from PyQt5.QtCore import Qt
import sflvault
from sflvault.clientqt.lib.auth import setSecret
import sflvault.clientqt
from sflvault.client import SFLvaultClient
import shutil
import os
try:
    import keyring
except:
    pass


class PreferencesWidget(QtWidgets.QDialog):
    def __init__(self, parent=None):
        QtWidgets.QDialog.__init__(self, parent)
        self.parent = parent
        self.settings = self.parent.settings
        self.wizard = False

        # Load gui items
        self.save = QtWidgets.QPushButton(self.tr("Save"))
        self.cancel = QtWidgets.QPushButton(self.tr("Cancel"))

        self.usernameLabel = QtWidgets.QLabel(self.tr("User name"))
        self.username = QtWidgets.QLineEdit()
        self.urlLabel = QtWidgets.QLabel(self.tr("Vault server address"))
        self.url = QtWidgets.QLineEdit()
        self.wallet_label = QtWidgets.QLabel(self.tr("Wallet configuration"))
        self.configure_wallet = QtWidgets.QPushButton(self.tr("Configure Wallet"))
        self.saveMainWindowLabel = QtWidgets.QLabel(self.tr("Save dock positions"))
        self.saveMainWindow = QtWidgets.QCheckBox()
        self.autoConnectLabel = QtWidgets.QLabel(self.tr("Auto connect"))
        self.autoConnect = QtWidgets.QCheckBox()
        self.systrayLabel = QtWidgets.QLabel(self.tr("Show system tray"))
        self.systray = QtWidgets.QCheckBox()
        self.effectsLabel = QtWidgets.QLabel(self.tr("Enabled effects"))
        self.effects = QtWidgets.QCheckBox()
        self.hideLabel = QtWidgets.QLabel(self.tr("Hide on close"))
        self.hide = QtWidgets.QCheckBox()
        self.webpreviewLabel = QtWidgets.QLabel(self.tr("Web preview"))
        self.webpreview = QtWidgets.QCheckBox()
        self.filterLabel = QtWidgets.QLabel(self.tr("Filter bar"))
        self.filter = QtWidgets.QCheckBox()
        self.minSearchLabel = QtWidgets.QLabel(self.tr("Minimum search"))
        self.minSearch = QtWidgets.QSpinBox()
        self.minSearch.setMinimum(0)
        self.minSearch.setMaximum(10)
        self.osdLabel = QtWidgets.QLabel(self.tr("Osd show time"))
        self.osd = QtWidgets.QSpinBox()
        self.osd.setMinimum(0)
        self.osd.setMaximum(500)
        self.languageLabel = QtWidgets.QLabel(self.tr("Language"))
        self.language = QtWidgets.QComboBox()

        # Vault Group Box
        vaultbox = QtWidgets.QGroupBox(self.tr("SFLvault preferences"))
        gridLayout = QtWidgets.QGridLayout()
        gridLayout.addWidget(self.usernameLabel,0,0)
        gridLayout.addWidget(self.username,0,1,)
        gridLayout.addWidget(self.urlLabel,1,0)
        gridLayout.addWidget(self.url,1,1,)
        gridLayout.addWidget(self.wallet_label,2,0)
        gridLayout.addWidget(self.configure_wallet,2,1)
        vaultbox.setLayout(gridLayout)

        # Gui Group box
        guibox = QtWidgets.QGroupBox(self.tr("GUI preferences"))
        gridLayout = QtWidgets.QGridLayout()
        gridLayout.addWidget(self.saveMainWindowLabel,0,0)
        gridLayout.addWidget(self.saveMainWindow,0,1)
        gridLayout.addWidget(self.autoConnectLabel,1,0)
        gridLayout.addWidget(self.autoConnect,1,1)
        gridLayout.addWidget(self.systrayLabel,2,0)
        gridLayout.addWidget(self.systray,2,1)
        gridLayout.addWidget(self.effectsLabel,3,0)
        gridLayout.addWidget(self.effects,3,1)
        gridLayout.addWidget(self.hideLabel,4,0)
        gridLayout.addWidget(self.hide,4,1)
        gridLayout.addWidget(self.webpreviewLabel,5,0)
        gridLayout.addWidget(self.webpreview,5,1)
        gridLayout.addWidget(self.filterLabel,6,0)
        gridLayout.addWidget(self.filter,6,1)
        gridLayout.addWidget(self.minSearchLabel,7,0)
        gridLayout.addWidget(self.minSearch,7,1)
        gridLayout.addWidget(self.osdLabel,8,0)
        gridLayout.addWidget(self.osd,8,1)
        gridLayout.addWidget(self.languageLabel,9,0)
        gridLayout.addWidget(self.language,9,1)
        guibox.setLayout(gridLayout)

        # Positionning items
        buttonLayout = QtWidgets.QHBoxLayout()
        buttonLayout.addStretch(1)
        buttonLayout.addWidget(self.cancel)
        buttonLayout.addWidget(self.save)

        mainLayout = QtWidgets.QVBoxLayout()
        mainLayout.addWidget(vaultbox)
        mainLayout.addWidget(guibox)
        mainLayout.addLayout(buttonLayout)
        self.setLayout(mainLayout)

        self.setWindowTitle(self.tr("Preferences"))
        self.resize(500,400)

        # SIGNALS
        self.save.clicked.connect(self.saveConfig)
        self.cancel.clicked.connect(self.reject)
        self.configure_wallet.clicked.connect(self.parent.savePassword)


    def exec_(self):
        # load config
        self.readConfig()
        # Show dialog
        self.show()

    def readConfig(self):
        """ ReadConfig
        """
        self.username.setText(self.settings.value("SFLvault/username", ""))
        self.url.setText(self.settings.value("SFLvault/url", ""))
        self.saveMainWindow.setCheckState(int(self.settings.value("SFLvault-qt4/savewindow", 0)))
        self.autoConnect.setCheckState(int(self.settings.value("SFLvault-qt4/autoconnect", 0)))
        self.systray.setCheckState(int(self.settings.value("SFLvault-qt4/systray", 0)))
        self.effects.setCheckState(int(self.settings.value("SFLvault-qt4/effects", 0)))
        self.hide.setCheckState(int(self.settings.value("SFLvault-qt4/hide", 0)))
        self.webpreview.setCheckState(int(self.settings.value("SFLvault-qt4/webpreview", 0)))
        self.filter.setCheckState(int(self.settings.value("SFLvault-qt4/filter", 0)))
        self.minSearch.setValue(int(self.settings.value("SFLvault-qt4/minsearch", 0)))
        self.osd.setValue(int(self.settings.value("osd/timer", 0)))
        self.fillLanguage(self.settings.value("SFLvault-qt4/language", ""))
#        self.fillWallet()

    def saveConfig(self):
        """ Save configuration
        """
        self.settings.setValue("SFLvault/username", self.username.text())
        self.settings.setValue("SFLvault/url", self.url.text())
        self.settings.setValue("SFLvault-qt4/savewindow", self.saveMainWindow.checkState())
        self.settings.setValue("SFLvault-qt4/autoconnect", self.autoConnect.checkState())
        self.settings.setValue("SFLvault-qt4/systray", self.systray.checkState())
        self.settings.setValue("SFLvault-qt4/effects", self.effects.checkState())
        self.settings.setValue("SFLvault-qt4/hide", self.hide.checkState())
        self.settings.setValue("SFLvault-qt4/webpreview", self.webpreview.checkState())
        self.settings.setValue("SFLvault-qt4/filter", self.filter.checkState())
        self.settings.setValue("SFLvault-qt4/minsearch", self.minSearch.value())
        self.settings.setValue("osd/timer", self.osd.value())
        self.settings.setValue("SFLvault-qt4/language", self.language.currentText())
        self.parent.loadUnloadSystrayConfig()
        self.parent.disEnableEffectsConfig()
        self.parent.showHideFilterBarConfig()
        self.parent.webpreviewConfig()
        # Close dialog
        self.accept()

    def fillLanguage(self, value):
        self.language.clear()
        i18n_dir = os.path.join(os.path.dirname(sflvault.clientqt.__file__),
                                'i18n')
        for file in os.listdir(i18n_dir):
            filename, ext = os.path.splitext(file)
            if ext == ".qm":
                appname, lang = filename.split("_",1)
                self.language.addItem(lang)
                if lang == value:
                    self.language.setCurrentIndex(self.language.count()-1)

