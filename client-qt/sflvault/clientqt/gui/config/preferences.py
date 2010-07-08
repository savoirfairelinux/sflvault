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
from PyQt4 import QtCore, QtGui
import re
from PyQt4.QtCore import Qt
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


class PreferencesWidget(QtGui.QDialog):
    def __init__(self, parent=None):
        QtGui.QDialog.__init__(self, parent)
        self.parent = parent
        self.settings = self.parent.settings
        self.wizard = False

        # Load gui items
        self.save = QtGui.QPushButton(self.tr("Save"))
        self.cancel = QtGui.QPushButton(self.tr("Cancel"))

        self.usernameLabel = QtGui.QLabel(self.tr("User name"))
        self.username = QtGui.QLineEdit()
        self.urlLabel = QtGui.QLabel(self.tr("Vault server address"))
        self.url = QtGui.QLineEdit()
        self.wallet_label = QtGui.QLabel(self.tr("Wallet configuration"))
        self.configure_wallet = QtGui.QPushButton(self.tr("Configure Wallet"))
        self.saveMainWindowLabel = QtGui.QLabel(self.tr("Save dock positions"))
        self.saveMainWindow = QtGui.QCheckBox()
        self.autoConnectLabel = QtGui.QLabel(self.tr("Auto connect"))
        self.autoConnect = QtGui.QCheckBox()
        self.systrayLabel = QtGui.QLabel(self.tr("Show system tray"))
        self.systray = QtGui.QCheckBox()
        self.effectsLabel = QtGui.QLabel(self.tr("Enabled effects"))
        self.effects = QtGui.QCheckBox()
        self.hideLabel = QtGui.QLabel(self.tr("Hide on close"))
        self.hide = QtGui.QCheckBox()
        self.webpreviewLabel = QtGui.QLabel(self.tr("Web preview"))
        self.webpreview = QtGui.QCheckBox()
        self.filterLabel = QtGui.QLabel(self.tr("Filter bar"))
        self.filter = QtGui.QCheckBox()
        self.minSearchLabel = QtGui.QLabel(self.tr("Minimum search"))
        self.minSearch = QtGui.QSpinBox()
        self.minSearch.setMinimum(0)
        self.minSearch.setMaximum(10)
        self.osdLabel = QtGui.QLabel(self.tr("Osd show time"))
        self.osd = QtGui.QSpinBox()
        self.osd.setMinimum(0)
        self.osd.setMaximum(500)
        self.languageLabel = QtGui.QLabel(self.tr("Language"))
        self.language = QtGui.QComboBox()

        # Vault Group Box
        vaultbox = QtGui.QGroupBox(self.tr("SFLvault preferences"))
        gridLayout = QtGui.QGridLayout()
        gridLayout.addWidget(self.usernameLabel,0,0)
        gridLayout.addWidget(self.username,0,1,)
        gridLayout.addWidget(self.urlLabel,1,0)
        gridLayout.addWidget(self.url,1,1,)
        gridLayout.addWidget(self.wallet_label,2,0)
        gridLayout.addWidget(self.configure_wallet,2,1)
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
        self.resize(500,400)

        # SIGNALS
        QtCore.QObject.connect(self.save,
                                QtCore.SIGNAL("clicked()"),
                                self.saveConfig)
        QtCore.QObject.connect(self.cancel,
                                QtCore.SIGNAL("clicked()"),
                                self, QtCore.SLOT("reject()"))
        QtCore.QObject.connect(self.configure_wallet,
                                QtCore.SIGNAL("clicked()"),
                                self.parent.savePassword)


    def exec_(self):
        # load config
        self.readConfig()
        # Show dialog
        self.show()

    def readConfig(self):
        """ ReadConfig
        """
        self.username.setText(self.settings.value("SFLvault/username").toString())
        self.url.setText(self.settings.value("SFLvault/url").toString())
        self.saveMainWindow.setCheckState(self.settings.value("SFLvault-qt4/savewindow").toInt()[0])
        self.autoConnect.setCheckState(self.settings.value("SFLvault-qt4/autoconnect").toInt()[0])
        self.systray.setCheckState(self.settings.value("SFLvault-qt4/systray").toInt()[0])
        self.effects.setCheckState(self.settings.value("SFLvault-qt4/effects").toInt()[0])
        self.hide.setCheckState(self.settings.value("SFLvault-qt4/hide").toInt()[0])
        self.webpreview.setCheckState(self.settings.value("SFLvault-qt4/webpreview").toInt()[0])
        self.filter.setCheckState(self.settings.value("SFLvault-qt4/filter").toInt()[0])
        self.minSearch.setValue(self.settings.value("SFLvault-qt4/minsearch").toInt()[0])
        self.osd.setValue(self.settings.value("osd/timer").toInt()[0])
        self.fillLanguage(self.settings.value("SFLvault-qt4/language").toString())
#        self.fillWallet()

    def saveConfig(self):
        """ Save configuration
        """
        self.settings.setValue("SFLvault/username", QtCore.QVariant(self.username.text()))
        self.settings.setValue("SFLvault/url", QtCore.QVariant(self.url.text()))
        self.settings.setValue("SFLvault-qt4/savewindow", QtCore.QVariant(self.saveMainWindow.checkState()))
        self.settings.setValue("SFLvault-qt4/autoconnect", QtCore.QVariant(self.autoConnect.checkState()))
        self.settings.setValue("SFLvault-qt4/systray", QtCore.QVariant(self.systray.checkState()))
        self.settings.setValue("SFLvault-qt4/effects", QtCore.QVariant(self.effects.checkState()))
        self.settings.setValue("SFLvault-qt4/hide", QtCore.QVariant(self.hide.checkState()))
        self.settings.setValue("SFLvault-qt4/webpreview", QtCore.QVariant(self.webpreview.checkState()))
        self.settings.setValue("SFLvault-qt4/filter", QtCore.QVariant(self.filter.checkState()))
        self.settings.setValue("SFLvault-qt4/minsearch", QtCore.QVariant(self.minSearch.value()))
        self.settings.setValue("osd/timer", QtCore.QVariant(self.osd.value()))
        self.settings.setValue("SFLvault-qt4/language", QtCore.QVariant(self.language.currentText()))
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

