#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
#    sqlvault_qt/mainWindow.py 
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
from .tree.tree import TreeVault, TreeView
from .docks.infodock import InfoDock
from .docks.searchdock import SearchDock
from .docks.aliasdock import AliasDock
from .config.protocols import ProtocolsWidget
from .config.users import UsersWidget
from .config.preferences import PreferencesWidget
#from config.configfile import ConfigFileWidget
from .config.config import Config
from .config.customer import EditCustomerWidget, DeleteCustomerWidget
from .config.machine import EditMachineWidget, DeleteMachineWidget
from .config.service import EditServiceWidget, DeleteServiceWidget
from .dialog.aboutdialog import AboutDialog, About_sflvaultqt_dialog, Help_dialog
from .wizard.initaccount import InitAccount
from .wizard.savepassword import SavePasswordWizard
from .bar.menubar import MenuBar
from .bar.systray import Systray
from .bar.osd import Osd
from sflvault.client import SFLvaultClient
import shutil
import os
from sflvault.clientqt.lib.error import *
from sflvault.clientqt.lib.auth import *
import platform
import shlex



class MainWindow(QtWidgets.QMainWindow):
    def __init__(self, app=None, parent=None):
        QtWidgets.QMainWindow.__init__(self, parent)
        self.parent = parent
        self.translator = QtCore.QTranslator() 
        self.app = app
        self.listWidget = {}
        self.userinfo = None
        self.search_timer = QtCore.QTimer()

        # Set main window title
        self.setWindowTitle("SFLvault Client")

        # Load settings
        self.settings = Config(parent=self)

        # Load language
        self.setLanguage()
        # Load GUI item
        self.treewidget = TreeVault(parent=self)
        self.tree = self.treewidget.tree
        self.menubar = MenuBar(parent=self)
        self.aliasdock = AliasDock(parent=self)
        self.aliasdock.setObjectName("aliases")
        self.searchdock = SearchDock(parent=self)
        self.searchdock.setObjectName("search")
        self.infodock = InfoDock(parent=self)
        self.infodock.setObjectName("info")
        self.systray = Systray(parent=self)

        # Create clipboard
        self.clipboard = QtWidgets.QApplication.clipboard()

        # Load alias list
        self.alias_list = self.aliasdock.alias.alias_list

        # Attach items to mainwindow
        self.setCentralWidget(self.treewidget)
        self.addDockWidget(QtCore.Qt.LeftDockWidgetArea,self.aliasdock)
        self.listWidget['alias'] = self.aliasdock
        self.addDockWidget(QtCore.Qt.RightDockWidgetArea,self.searchdock)
        self.listWidget['search'] = self.searchdock
        self.addDockWidget(QtCore.Qt.RightDockWidgetArea,self.infodock)
        self.listWidget['info'] = self.infodock

        # Load Menu bar
        self.setMenuBar(self.menubar)

        # Read aliases
        self.aliasdock.readAliases()

        # Load windows
        self.protocols = ProtocolsWidget(parent=self)
        self.users = UsersWidget(parent=self)
        self.preferences = PreferencesWidget(parent=self)
#        self.configfile = ConfigFileWidget(parent=self)
        # Load shortcut
        self.setShortcut()

        # Signals
        ## Quit
        self.menubar.quit.triggered.connect(self.app.quit)
        ## Protocols
        self.menubar.protocols.triggered.connect(self.protocols.exec_)
        ## Protocols
        self.menubar.quickconnect.triggered.connect(self.quickConnection)
        ## Users & Groups
        self.menubar.users.triggered.connect(self.users.exec_)
        ## Save Vault password
        self.menubar.savepass.triggered.connect(self.savePassword)
        ## First Vault connection
        self.menubar.firstconnection.triggered.connect(self.firstConnection)
        ## Vault connection
        self.menubar.connection.triggered.connect(self.vaultConnection)
        ## Preferences
        self.menubar.preferences.triggered.connect(self.preferences.exec_)
        ## Set config file
#        QtCore.QObject.connect(self.menubar.configfile, QtCore.SIGNAL("triggered()"), self.configfile.exec_)
        ## Show search dock
        self.menubar.search.triggered.connect(self.searchdock.setVisible)
        ## Show info dock
        self.menubar.info.triggered.connect(self.infodock.setVisible)
        ## Show alias dock
        self.menubar.alias.triggered.connect(self.aliasdock.setVisible)
        ## new customer
        self.menubar.newcust.triggered.connect(self.editCustomer)
        ## new machine
        self.menubar.newmach.triggered.connect(self.editMachine)
        ## new service
        self.menubar.newserv.triggered.connect(self.editService)
        ## about
        self.menubar.sflvaultabout.triggered.connect(self.showAbout)
        self.menubar.qtabout.triggered.connect(self.show_qt_about)
        self.menubar.sflvaulthelp.triggered.connect(self.show_help)

        geometry = self.settings.value("SFLvault-qt4/binsavewindow")
        if geometry is not None:
            self.restoreGeometry(geometry)

    def show_help(self):
        helpd = Help_dialog(self)
        helpd.open()
        helpd.show()

    def showAbout(self):
        about = AboutDialog(self)
        about.open()
        about.show()
 
    def show_qt_about(self):
        about = About_sflvaultqt_dialog(self)
        about.open()
        about.show()

    def closeEvent(self, event):
        if int(self.settings.value("SFLvault-qt4/hide", 0)) == QtCore.Qt.Checked:
            event.ignore()
            state = self.saveGeometry()
            self.settings.setValue("SFLvault-qt4/binsavewindow", state)
            self.hide()
        elif int(self.settings.value("SFLvault-qt4/savewindow", 0)) == QtCore.Qt.Checked:
            state = self.saveGeometry()
            self.settings.setValue("SFLvault-qt4/binsavewindow", state)

    def searchWaiting(self, research):
        """ Waiting timer end
        """
        if self.search_timer.isActive():
            self.search_timer.stop()
        self.search_timer.start(1000)


    def search(self, research=None):
        """
            Search item in sflvault
        """
        if self.search_timer.isActive():
            self.search_timer.stop()
        # Get select group
        groups = self.searchdock.search.groups.itemData(self.searchdock.search.groups.currentIndex())
        if groups is None:
            groups = None
        # Get research
        research = self.searchdock.search.search.text().split(" ")
        self.tree.search(research, groups)

    def showInformations(self, index):
        """
           Show informations
        """
        if isinstance(index, QtCore.QItemSelection):
            # if no items are selected do nothing...
            if not index.indexes():
                return None
            index = index.indexes()[0]
        # Get Id colunm
        if len(self.tree.selectedIndexes()) < 2:
            return None 
        indexId = self.tree.selectedIndexes()[1]

        # Check if selected item is an customer, machine or service
        if index.parent().isValid():
            # Selected item is a machine or service
            if index.parent().parent().isValid():
                # Selected item is a service
                # Get service parent id (machineid)
                parentIndex = self.tree.proxyModel.parent(index)
                # Get column 1 (id column)
                parentIndex1 = self.tree.proxyModel.index(parentIndex.row(), 1, parentIndex.parent())
                idmach = str(self.tree.proxyModel.data(parentIndex1, QtCore.Qt.DisplayRole))
                idmach = int(idmach.split("#")[1])
                # Get machine parent id (customerid)
                parentIndex = self.tree.proxyModel.parent(parentIndex)
                parentIndex1 = self.tree.proxyModel.index(parentIndex.row(), 1, parentIndex.parent())
                idcust = str(self.tree.proxyModel.data(parentIndex1, QtCore.Qt.DisplayRole))
                idcust = int(idcust.split("#")[1])
                # Get service id 
                idserv = str(indexId.data(QtCore.Qt.DisplayRole))
                idserv = int(idserv.split("#")[1])
            else:
                # Selected item is a machine
                # Get machine parent id (customerid)
                parentIndex = self.tree.proxyModel.parent(index)
                parentIndex1 = self.tree.proxyModel.index(parentIndex.row(), 1, parentIndex.parent())
                idcust = str(self.tree.proxyModel.data(parentIndex1, QtCore.Qt.DisplayRole))
                idcust = int(idcust.split("#")[1])
                # Get machine id 
                idmach = str(indexId.data(QtCore.Qt.DisplayRole))
                try:
                    idmach = int(idmach.split("#")[1])
                except ValueError as e:
                    idmach = None
                idserv = None
        else:
            # Selected item is a customer
            idcust = str(indexId.data(QtCore.Qt.DisplayRole))
            idcust = int(idcust.split("#")[1])
            idmach = None
            idserv = None
        
        self.infodock.showInformations(idcust, machineid=idmach, serviceid=idserv)

    def GetIdByTree(self, index=None):
        """
            Get selected item id in tree and launch connection
        """
        # Get Id colunm
        if index == None:
            index = self.tree.selectedIndexes()[0]
        indexId = self.tree.selectedIndexes()[1]
        idserv = str(indexId.data(QtCore.Qt.DisplayRole))
        idserv = int(idserv.split("#")[1])
        # Check if seleted item is a service
        if index.parent().parent().isValid():
            self.connection(idserv)

    def GetIdByBookmark(self, index=None):
        """
            Get selected item id in bookmark and launch connection
        """
        # Get Id colunm
        indexId = self.alias_list.selectedIndexes()[1]
        idserv = str(indexId.data(QtCore.Qt.DisplayRole))
        idserv = int(idserv.split("#")[1])
        # Check if seleted item is a service
        self.connection(idserv)


    def show_tooltip_by_bookmark(self, index=None):
        """ Get selected item id in bookmark and show password
        """
        # Get Id colunm
        indexId = self.alias_list.selectedIndexes()[1]
        idserv = str(indexId.data(QtCore.Qt.DisplayRole))
        idserv = int(idserv.split("#")[1])
        # Check if seleted item is a service
        self.connection(idserv,True)


    def show_tooltip(self, index=None):
        """ Get selected item id in tree and show password
        """
        # Get Id colunm
        if index == None:
            index = self.tree.selectedIndexes()[0]
        indexId = self.tree.selectedIndexes()[1]
        idserv = str(indexId.data(QtCore.Qt.DisplayRole))
        idserv = int(idserv.split("#")[1])
        # Check if seleted item is a service
        if index.parent().parent().isValid():
            self.connection(idserv,True)

    def connection(self, idserv, show_tooltip=False, tunnel=False):
        """
            Connect to a service
        """
        # Get Options
        options = {}
        # Check if we can access to this service
        password = getPassword(idserv)
        # getPassword return None
        # means you can't access to this service
        if not password:
            # Do nothing
            return False
        # Check if the service exist
        service = getService(idserv)
        if not service:
            return False
        # Get service
        # Check if url have several @
        username = None
        if len(service["services"][-1]["url"].split("@")) > 2:
            temp = service["services"][-1]["url"].rsplit("@",1)
            username = temp[0].split("://")[-1]
            protocol = temp[0].split("://")[0]
            url = temp[1]
            url = QtCore.QUrl(protocol + "://" + url)
        else:
            url = QtCore.QUrl(service["services"][-1]["url"])
        protocol = str(url.scheme())
        port = str(url.port())
        address  = str(url.host() + ":" + str(port) + url.path()) if port != "-1" else str(url.host() + url.path())
        # Copy password to clipboard if checked in config
        clip = int(self.settings.value("protocols/" + protocol + "/clip", 0))
        if clip == QtCore.Qt.Checked:
            self.copyToClip(password)
        # Prepare dictionnary
        if username:
            options["user"] = username
        elif url.userName():
            options["user"] = url.userName()
        else:
            options["user"] = None
        options["address"] = address

        options["port"] = port
        options["protocol"] = protocol
        options["vaultid"] = int(service["services"][-1]["id"])
        if tunnel:
            # TODO Fix option
            options["vaultconnect"] = "sflvault connect %s -- %s" % (options["vaultid"], tunnel)
        else:
            options["vaultconnect"] = "sflvault connect %s" % options["vaultid"]
        # Show Tooltip if checked in config
        tooltip = int(self.settings.value("protocols/" + protocol + "/tooltip", 0))
        if tooltip == QtCore.Qt.Checked or \
           not self.settings.value("protocols/" + protocol + "/command", "")\
           or show_tooltip:
            self.osd = Osd(password=password, username=options["user"], address=options["address"], parent=self)
            self.osd.show()
            if show_tooltip:
                # If tooltip == True then we just want to show password
                return True
        # Prepare to launch command
        command = self.settings.value("protocols/" + protocol + "/command", "")
        if command:
            # Create Command
            args = self.settings.value("protocols/" + protocol + "/args", "")
            command = self.settings.value("protocols/" + protocol + "/command", "")
            args = args % options
            print(" ".join([command, args]))
            args = [str(arg) for arg in shlex.split(args)]
            args_list = list(args)
            
            # Exit if command is empty (to prevent segfault. See bug #4)
            if command.strip() == "":
                return
            # Launch process
            self.procxterm = QtCore.QProcess()
            self.procxterm.start(command, args_list)

    def copyToClip(self, password):
        """
            Paste password to the clipboard
        """
        self.clipboard.setText(password)

    def vaultConnection(self):
        """
            Connect to the vault
        """
        token = getAuth()
        if not token:
            return False

        # Get your informations
        self.userinfo = getUserInfo(self.settings.value("SFLvault/username", ""))

        ## "Connect" Alias
        self.aliasdock.alias.alias_list.doubleClicked.connect(self.GetIdByBookmark)
        self.aliasdock.alias.alias_list.connectAct.triggered.connect(self.GetIdByBookmark)
        self.aliasdock.alias.alias_list.showAct.triggered.connect(lambda checked: self.show_tooltip_by_bookmark())

        # "Connect" search dock
        ## Update Group list in search box
        self.searchdock.connection()

        # "Connect" tree
        self.treewidget.connection()
        ## Tree Search
        self.searchdock.search.search.textEdited.connect(self.searchWaiting)
        self.search_timer.timeout.connect(self.search)
        self.searchdock.search.search.returnPressed.connect(self.focusOnTree)
        ## Tree filter by groups
        self.searchdock.search.groups.currentIndexChanged.connect(self.search)
        ## Tree menu
        self.tree.bookmarkAct.triggered.connect(self.aliasdock.alias.model.addAlias)
        self.tree.editAct.triggered.connect(self.editItem)
        self.tree.delAct.triggered.connect(self.delItem)
        self.tree.newServiceAct.triggered.connect(self.addService)
        self.tree.newMachineAct.triggered.connect(self.addMachine)
        self.tree.tunnelAct.triggered.connect(self.tunnel)
        self.tree.connectAct.triggered.connect(self.GetIdByTree)
        self.tree.showAct.triggered.connect(lambda checked: self.show_tooltip())
        ## Tree connection
        self.tree.doubleClicked.connect(self.GetIdByTree)
        ## Tree item informations
        self.tree.clicked.connect(self.showInformations)
        self.tree.selectionModel().selectionChanged.connect(self.showInformations)
        ## Tree Filter
        self.treewidget.filter.filter_input.returnPressed.connect(self.focusOnTree)

        # "Connect" menus
        self.menubar.enableItems()

        # Show all services
        self.search(None)

    def exec_(self):
        """
            Show default and load dock positions if necessary
        """
        if int(self.settings.value("SFLvault-qt4/savewindow", 0)) == QtCore.Qt.Checked:
            geometry = self.settings.value("SFLvault-qt4/binsavewindow")
            if geometry:
                self.restoreState(geometry)
        if int(self.settings.value("SFLvault-qt4/autoconnect", 0)) == QtCore.Qt.Checked:
            self.vaultConnection()
        self.loadUnloadSystrayConfig()
        self.disEnableEffectsConfig()
        self.showHideFilterBarConfig()
        self.webpreviewConfig()
        self.show()

    def loadUnloadSystrayConfig(self):
        """
            Load or unload systray
        """
        if int(self.settings.value("SFLvault-qt4/systray", 0)) == QtCore.Qt.Checked:
            self.systray.show()
        elif int(self.settings.value("SFLvault-qt4/systray", 0)) == QtCore.Qt.Unchecked:
            self.systray.hide()


    def disEnableEffectsConfig(self):
        """
            Enable or not effects
        """
        if int(self.settings.value("SFLvault-qt4/effects", 0)) == QtCore.Qt.Checked:
            self.setAnimated(True)
            self.tree.setAnimated(True)
        elif int(self.settings.value("SFLvault-qt4/effects", 0)) == QtCore.Qt.Unchecked:
            self.setAnimated(False)
            self.tree.setAnimated(False)

    def showHideFilterBarConfig(self):
        """
            Show or hide filter bar
        """
        if int(self.settings.value("SFLvault-qt4/filter", 0)) == QtCore.Qt.Checked:
            self.treewidget.filter.show()
        elif int(self.settings.value("SFLvault-qt4/filter", 0)) == QtCore.Qt.Unchecked:
            self.treewidget.filter.hide()
            self.treewidget.filter.filter_input.setText("")
 
    def webpreviewConfig(self):
        if int(self.settings.value("SFLvault-qt4/webpreview", 0)) == QtCore.Qt.Checked:
            self.tree.entered.connect(self.tree.startTimer)
            self.tree.timer.timeout.connect(self.tree.showWebPreview)
            self.tree.viewportEntered.connect(self.tree.timerStop)
        elif int(self.settings.value("SFLvault-qt4/webpreview", 0)) == QtCore.Qt.Unchecked:
            try:
                self.tree.entered.disconnect(self.tree.startTimer)
            except (TypeError, RuntimeError):
                pass
            try:
                self.tree.timer.timeout.disconnect(self.tree.showWebPreview)
            except (TypeError, RuntimeError):
                pass
            try:
                self.tree.viewportEntered.disconnect(self.tree.timerStop)
            except (TypeError, RuntimeError):
                pass

    def setLanguage(self):
        """
            Load language
        """
        lang = self.settings.value("SFLvault-qt4/language", "")
        if lang:
            bool = self.translator.load("sflvault-qt4_" + lang, "./i18n", "_", ".qm")
            # If not language loaded, print message
            if not bool:
                print(self.tr("Warning : unable to load i18n/sflvault-qt4_" + lang))

            self.app.installTranslator(self.translator)

    def setShortcut(self):
        """
            Set shortcuts
        """
        sc1 = QtWidgets.QShortcut(QtGui.QKeySequence(QtCore.Qt.CTRL + QtCore.Qt.Key_I), self)
        sc1.activated.connect(self.showHideFilterShort)
        sc2 = QtWidgets.QShortcut(QtGui.QKeySequence(QtCore.Qt.CTRL + QtCore.Qt.Key_F), self)
        sc2.activated.connect(self.searchShort)
        sc3 = QtWidgets.QShortcut(QtGui.QKeySequence(QtCore.Qt.CTRL + QtCore.Qt.Key_T), self)
        sc3.activated.connect(self.focusOnTree)

    def searchShort(self):
        """
            Show search dock and set focus
        """
        if not self.searchdock.isVisible():
            self.searchdock.show()
        self.searchdock.search.search.setFocus()

    def showHideFilterShort(self):
        """
            Hide or show filter bar
        """
        if self.treewidget.filter.isVisible() and self.treewidget.filter.filter_input.hasFocus():
            self.treewidget.filter.hide()
            self.treewidget.filter.filter_input.setText("")
        elif self.treewidget.filter.isVisible() and not self.treewidget.filter.filter_input.hasFocus():
            self.treewidget.filter.filter_input.setFocus()
        else:
            self.treewidget.filter.show()
            self.treewidget.filter.filter_input.setFocus()

    def focusOnTree(self):
        """
            Set Focus on vault tree and select first item
        """
        self.tree.setFocus()
        if not self.tree.selectedIndexes():
            # Get column widths to selected it
            name_column_width = self.tree.columnWidth(0)
            id_column_width = self.tree.columnWidth(1)
            # Select first row and first column
            self.tree.setSelection(QtCore.QRect(0, 0, name_column_width, 16), QtCore.QItemSelectionModel.Select)
            # Select first row and second column
            self.tree.setSelection(QtCore.QRect(name_column_width, 0, id_column_width, 16), QtCore.QItemSelectionModel.Select)

    def quickConnection(self):
        """
            Launch connection from shortcut
        """
        ret, ok = QtWidgets.QInputDialog.getText(self.parent, self.tr("Quick connection"),
                                                 self.tr("Service id or service alias :"),
                                                 QtWidgets.QLineEdit.Normal)
        if not ok or not ret:
            return False

        # Try to know if id is a integer
        try:
            id = int(ret)
        except ValueError:
            id = None
            ret = str(ret)
            if ret.startswith("s#"):
                id = ret.split("#")[1]
            if not id:
                id = getAlias(ret)
                if id:
                    id = id.split("#")[1]
        # Finally launch connection
        if id:
            self.connection(id)
        else:
            ErrorMessage("No service found")

    def editCustomer(self, custid=False):
        self.editcustomer = EditCustomerWidget(custid, parent=self)
        self.editcustomer.exec_()

    def editMachine(self, machid=False):
        self.editmachine = EditMachineWidget(machid, parent=self)
        self.editmachine.exec_()

    def editService(self, servid=False):
        self.editservice = EditServiceWidget(servid, parent=self)
        self.editservice.exec_()

    def editItem(self):
        # Get Id colunm
        indexId = self.tree.selectedIndexes()[1]
        index = self.tree.selectedIndexes()[0]
        itemid = str(indexId.data(QtCore.Qt.DisplayRole))
        try:
            itemid = int(itemid.split("#")[1])
        except ValueError as e:
            return False
        # Check if seleted item is a service
        if index.parent().parent().isValid():
            self.editService(itemid)
        # Check if seleted item is a machine
        elif index.parent().isValid():
            self.editMachine(itemid)
        # Check if seleted item is a customer
        elif index.isValid():
            self.editCustomer(itemid)
        else:
            return False

    def delCustomer(self, custid=None):
        """
            # Ask Delete customer ?
        """
        self.delcustomer = DeleteCustomerWidget(custid, parent=self)
        self.delcustomer.exec_()

    def delMachine(self, machid=None):
        """
            # Ask Delete machine ?
        """
        self.delmachine = DeleteMachineWidget(machid, parent=self)
        self.delmachine.exec_()

    def delService(self, servid=None):
        """
            # Ask Delete service ?
        """
        self.delservice = DeleteServiceWidget(servid, parent=self)
        self.delservice.exec_()

    def delItem(self):
        # Get Id colunm
        indexId = self.tree.selectedIndexes()[1]
        index = self.tree.selectedIndexes()[0]
        itemid = str(indexId.data(QtCore.Qt.DisplayRole))
        try:
            itemid = int(itemid.split("#")[1])
        except ValueError as e:
            return False
        # Check if seleted item is a service
        if index.parent().parent().isValid():
            self.delService(itemid)
        # Check if seleted item is a machine
        elif index.parent().isValid():
            self.delMachine(itemid)
        # Check if seleted item is a customer
        elif index.isValid():
            self.delCustomer(itemid)
        else:
            return False

    def addMachine(self, machid=None, custid=None):
        """ Ask add a machine to selected customer
        """
        # Get Id colunm
        indexId = self.tree.selectedIndexes()[1]
        index = self.tree.selectedIndexes()[0]
        servid = str(indexId.data(QtCore.Qt.DisplayRole))
        servid = int(servid.split("#")[1])
        self.addmachine = EditMachineWidget(None, servid, parent=self)
        self.addmachine.exec_()

    def addService(self, machid=None, servid=None):
        """ Add a new service
        """
        # Get Id colunm
        indexId = self.tree.selectedIndexes()[1]
        index = self.tree.selectedIndexes()[0]
        machid = str(indexId.data(QtCore.Qt.DisplayRole))
        try:
            machid = int(machid.split("#")[1])
        except ValueError as e:
            return False
        self.addservice = EditServiceWidget(False, machid, parent=self)
        self.addservice.exec_()

    def tunnel(self):
        index = self.tree.selectedIndexes()[0]
        indexId = self.tree.selectedIndexes()[1]
        idserv = str(indexId.data(QtCore.Qt.DisplayRole))
        idserv = int(idserv.split("#")[1])

        tunnel,bool = QtWidgets.QInputDialog().getText(
                                    self,
                                    "SSH Tunnel",
                                    "Enter the ssh tunnel (ex: -L 5000:127.0.0.1:3306 )",
                                    QtWidgets.QLineEdit.Normal,
                                    "",
                                    )
        if not bool or tunnel == "":
            return False
        self.connection(idserv, show_tooltip=False, tunnel=tunnel)

    def addItem(self):
        # Get Id colunm
        indexId = self.tree.selectedIndexes()[1]
        index = self.tree.selectedIndexes()[0]
        itemid = str(indexId.data(QtCore.Qt.DisplayRole))
        itemid = int(itemid.split("#")[1])
        # Check if seleted item is a service
        if index.parent().parent().isValid():
            print(str(index.parent().data(QtCore.Qt.DisplayRole)))
            return False
            self.addService(itemid)
        # Check if seleted item is a machine
        elif index.parent().isValid():
            self.addMachine(itemid)
        # Check if seleted item is a customer
        elif index.isValid():
            self.addCustomer(itemid)
        else:
            return False

    def firstConnection(self):
        self.firstconnection = InitAccount(self)

    def savePassword(self, wallet_id=None):
        self.savepass = SavePasswordWizard(wallet_id=wallet_id, parent=self)
