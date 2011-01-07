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
from PyQt4 import QtCore, QtGui
import re
from PyQt4.QtCore import Qt
import sflvault
from tree.tree import TreeVault, TreeView
from docks.infodock import InfoDock
from docks.searchdock import SearchDock
from docks.aliasdock import AliasDock
from config.protocols import ProtocolsWidget
from config.users import UsersWidget
from config.preferences import PreferencesWidget
#from config.configfile import ConfigFileWidget
from config.config import Config
from config.customer import EditCustomerWidget, DeleteCustomerWidget
from config.machine import EditMachineWidget, DeleteMachineWidget
from config.service import EditServiceWidget, DeleteServiceWidget
from wizard.initaccount import InitAccount
from wizard.savepassword import SavePasswordWizard
from bar.menubar import MenuBar
from bar.systray import Systray
from bar.osd import Osd
from sflvault.client import SFLvaultClient
import shutil
import os
from sflvault.clientqt.lib.error import *
from sflvault.clientqt.lib.auth import *
import platform
import shlex



class MainWindow(QtGui.QMainWindow):
    def __init__(self, app=None, parent=None):
        QtGui.QMainWindow.__init__(self, parent)
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
        self.clipboard = QtGui.QApplication.clipboard()

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
        QtCore.QObject.connect(self.menubar.quit, QtCore.SIGNAL("triggered()"), self.app.quit)
        ## Protocols
        QtCore.QObject.connect(self.menubar.protocols, QtCore.SIGNAL("triggered()"), self.protocols.exec_)
        ## Protocols
        QtCore.QObject.connect(self.menubar.quickconnect, QtCore.SIGNAL("triggered()"), self.quickConnection)
        ## Users & Groups
        QtCore.QObject.connect(self.menubar.users, QtCore.SIGNAL("triggered()"), self.users.exec_)
        ## Save Vault password
        QtCore.QObject.connect(self.menubar.savepass, QtCore.SIGNAL("triggered()"), self.savePassword)
        ## First Vault connection
        QtCore.QObject.connect(self.menubar.firstconnection, QtCore.SIGNAL("triggered()"), self.firstConnection)
        ## Vault connection
        QtCore.QObject.connect(self.menubar.connection, QtCore.SIGNAL("triggered()"), self.vaultConnection)
        ## Preferences
        QtCore.QObject.connect(self.menubar.preferences, QtCore.SIGNAL("triggered()"), self.preferences.exec_)
        ## Set config file
#        QtCore.QObject.connect(self.menubar.configfile, QtCore.SIGNAL("triggered()"), self.configfile.exec_)
        ## Show search dock
        QtCore.QObject.connect(self.menubar.search, QtCore.SIGNAL("triggered(bool)"), self.searchdock.setShown)
        ## Show info dock
        QtCore.QObject.connect(self.menubar.info, QtCore.SIGNAL("triggered(bool)"), self.infodock.setShown)
        ## Show alias dock
        QtCore.QObject.connect(self.menubar.alias, QtCore.SIGNAL("triggered(bool)"), self.aliasdock.setShown)
        ## new customer
        QtCore.QObject.connect(self.menubar.newcust, QtCore.SIGNAL("triggered(bool)"), self.editCustomer)
        ## new machine
        QtCore.QObject.connect(self.menubar.newmach, QtCore.SIGNAL("triggered(bool)"), self.editMachine)
        ## new service
        QtCore.QObject.connect(self.menubar.newserv, QtCore.SIGNAL("triggered(bool)"), self.editService)

        geometry = self.settings.value("SFLvault-qt4/binsavewindow").toByteArray()
        self.restoreGeometry(geometry)


    def closeEvent(self, event):
        if self.settings.value("SFLvault-qt4/hide").toInt()[0] == QtCore.Qt.Checked:
            event.ignore()
            state = QtCore.QVariant(self.saveGeometry())
            self.settings.setValue("SFLvault-qt4/binsavewindow", state)
            self.hide()
        elif self.settings.value("SFLvault-qt4/savewindow").toInt()[0] == QtCore.Qt.Checked:
            state = QtCore.QVariant(self.saveGeometry())
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
        groups,bool = self.searchdock.search.groups.itemData(self.searchdock.search.groups.currentIndex()).toInt()
        if not bool:
            groups = None
        # Get research
        research = unicode(self.searchdock.search.search.text(), "latin-1").split(" ")
        self.tree.search(research, groups)

    def showInformations(self, index):
        """
           Show informations
        """
        if isinstance(index, QtGui.QItemSelection):
            # if no items are selected do nothing...
            if not index.indexes():
                return None
            index = index.indexes()[0]
        # Get Id colunm
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
                idmach = self.tree.proxyModel.data(parentIndex1, QtCore.Qt.DisplayRole).toString()
                idmach = int(idmach.split("#")[1])
                # Get machine parent id (customerid)
                parentIndex = self.tree.proxyModel.parent(parentIndex)
                parentIndex1 = self.tree.proxyModel.index(parentIndex.row(), 1, parentIndex.parent())
                idcust = self.tree.proxyModel.data(parentIndex1, QtCore.Qt.DisplayRole).toString()
                idcust = int(idcust.split("#")[1])
                # Get service id 
                idserv = indexId.data(QtCore.Qt.DisplayRole).toString()
                idserv = int(idserv.split("#")[1])
            else:
                # Selected item is a machine
                # Get machine parent id (customerid)
                parentIndex = self.tree.proxyModel.parent(index)
                parentIndex1 = self.tree.proxyModel.index(parentIndex.row(), 1, parentIndex.parent())
                idcust = self.tree.proxyModel.data(parentIndex1, QtCore.Qt.DisplayRole).toString()
                idcust = int(idcust.split("#")[1])
                # Get machine id 
                idmach = indexId.data(QtCore.Qt.DisplayRole).toString()
                try:
                    idmach = int(idmach.split("#")[1])
                except ValueError, e:
                    idmach = None
                idserv = None
        else:
            # Selected item is a customer
            idcust = indexId.data(QtCore.Qt.DisplayRole).toString()
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
        idserv = indexId.data(QtCore.Qt.DisplayRole).toString()
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
        idserv = indexId.data(QtCore.Qt.DisplayRole).toString()
        idserv = int(idserv.split("#")[1])
        # Check if seleted item is a service
        self.connection(idserv)


    def show_tooltip_by_bookmark(self, index=None):
        """ Get selected item id in bookmark and show password
        """
        # Get Id colunm
        indexId = self.alias_list.selectedIndexes()[1]
        idserv = indexId.data(QtCore.Qt.DisplayRole).toString()
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
        idserv = indexId.data(QtCore.Qt.DisplayRole).toString()
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
        protocol = unicode(url.scheme())
        port = unicode(url.port())
        address  = unicode(url.host() + ":" + unicode(port) + url.path()) if port != "-1" else unicode(url.host() + url.path())
        # Copy password to clipboard if checked in config
        clip, bool = self.settings.value("protocols/" + protocol + "/clip").toInt()
        if bool and clip == QtCore.Qt.Checked:
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
        tooltip, bool = self.settings.value("protocols/" + protocol + "/tooltip").toInt()
        if (bool and tooltip == QtCore.Qt.Checked) or \
           not self.settings.value("protocols/" + protocol + "/command").toString()\
           or show_tooltip:
            self.osd = Osd(password=password, username=options["user"], address=options["address"], parent=self)
            self.osd.show()
            if show_tooltip:
                # If tooltip == True then we just want to show password
                return True
        # Prepare to launch command
        command = unicode(self.settings.value("protocols/" + protocol + "/command").toString())
        if command:
            # Create Command
            args = unicode(self.settings.value("protocols/" + protocol + "/args").toString())
            command = unicode(self.settings.value("protocols/" + protocol + "/command").toString())
            args = args % options
            print " ".join([command, args])
            args = [QtCore.QString(arg) for arg in args.split(" ")]
            args_list = QtCore.QStringList(args)
             
            # Exit if command is empty (to prevent segfault. See bug #4)
            if command.strip() == "": return
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
        self.userinfo = getUserInfo(str(self.settings.value("SFLvault/username").toString()))

        ## "Connect" Alias
        QtCore.QObject.connect(self.aliasdock.alias.alias_list, QtCore.SIGNAL("doubleClicked (const QModelIndex&)"), self.GetIdByBookmark)
        QtCore.QObject.connect(self.aliasdock.alias.alias_list.connectAct, QtCore.SIGNAL("triggered()"), self.GetIdByBookmark)
        QtCore.QObject.connect(self.aliasdock.alias.alias_list.showAct, QtCore.SIGNAL("triggered()"), self.show_tooltip_by_bookmark)

        # "Connect" search dock
        ## Update Group list in search box
        self.searchdock.connection()

        # "Connect" tree
        self.treewidget.connection()
        ## Tree Search
        QtCore.QObject.connect(self.searchdock.search.search, QtCore.SIGNAL("textEdited (const QString&)"), self.searchWaiting)
        QtCore.QObject.connect(self.search_timer, QtCore.SIGNAL("timeout()"), self.search)
        QtCore.QObject.connect(self.searchdock.search.search, QtCore.SIGNAL("returnPressed ()"), self.focusOnTree)
        ## Tree filter by groups
        QtCore.QObject.connect(self.searchdock.search.groups, QtCore.SIGNAL("currentIndexChanged (const QString&)"), self.search)
        ## Tree menu
        QtCore.QObject.connect(self.tree.bookmarkAct, QtCore.SIGNAL("triggered()"), self.aliasdock.alias.model.addAlias)
        QtCore.QObject.connect(self.tree.editAct, QtCore.SIGNAL("triggered()"), self.editItem)
        QtCore.QObject.connect(self.tree.delAct, QtCore.SIGNAL("triggered()"), self.delItem)
        QtCore.QObject.connect(self.tree.newServiceAct, QtCore.SIGNAL("triggered()"), self.addService)
        QtCore.QObject.connect(self.tree.newMachineAct, QtCore.SIGNAL("triggered()"), self.addMachine)
        QtCore.QObject.connect(self.tree.tunnelAct, QtCore.SIGNAL("triggered()"), self.tunnel)
        QtCore.QObject.connect(self.tree.connectAct, QtCore.SIGNAL("triggered()"), self.GetIdByTree)
        QtCore.QObject.connect(self.tree.showAct, QtCore.SIGNAL("triggered()"), self.show_tooltip)
        ## Tree connection
        QtCore.QObject.connect(self.tree, QtCore.SIGNAL("doubleClicked (const QModelIndex&)"), self.GetIdByTree)
        ## Tree item informations
        QtCore.QObject.connect(self.tree, QtCore.SIGNAL("clicked (const QModelIndex&)"), self.showInformations)
        QtCore.QObject.connect(self.tree.selectionModel(), QtCore.SIGNAL("selectionChanged (const QItemSelection&,const QItemSelection&)"), self.showInformations)
        ## Tree Filter
        QtCore.QObject.connect(self.treewidget.filter.filter_input, QtCore.SIGNAL("returnPressed ()"), self.focusOnTree)

        # "Connect" menus
        self.menubar.enableItems()

        # Show all services
        self.search(None)

    def exec_(self):
        """
            Show default and load dock positions if necessary
        """
        if self.settings.value("SFLvault-qt4/savewindow").toInt()[0] == QtCore.Qt.Checked:
            if self.settings.value("SFLvault-qt4/binsavewindow").toByteArray():
                t = self.restoreState(self.settings.value("SFLvault-qt4/binsavewindow").toByteArray())
        if self.settings.value("SFLvault-qt4/autoconnect").toInt()[0] == QtCore.Qt.Checked:
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
        if self.settings.value("SFLvault-qt4/systray").toInt()[0] == QtCore.Qt.Checked:
            self.systray.show()
        elif self.settings.value("SFLvault-qt4/systray").toInt()[0] == QtCore.Qt.Unchecked:
            self.systray.hide()


    def disEnableEffectsConfig(self):
        """
            Enable or not effects
        """
        if self.settings.value("SFLvault-qt4/effects").toInt()[0] == QtCore.Qt.Checked:
            self.setAnimated(True)
            self.tree.setAnimated(True)
        elif self.settings.value("SFLvault-qt4/effects").toInt()[0] == QtCore.Qt.Unchecked:
            self.setAnimated(False)
            self.tree.setAnimated(False)

    def showHideFilterBarConfig(self):
        """
            Show or hide filter bar
        """
        if self.settings.value("SFLvault-qt4/filter").toInt()[0] == QtCore.Qt.Checked:
            self.treewidget.filter.show()
        elif self.settings.value("SFLvault-qt4/filter").toInt()[0] == QtCore.Qt.Unchecked:
            self.treewidget.filter.hide()
            self.treewidget.filter.filter_input.setText("")
 
    def webpreviewConfig(self):
        if self.settings.value("SFLvault-qt4/webpreview").toInt()[0] == QtCore.Qt.Checked:
            QtCore.QObject.connect(self.tree,QtCore.SIGNAL("entered (const QModelIndex&)"), self.tree.startTimer)
            QtCore.QObject.connect(self.tree.timer, QtCore.SIGNAL("timeout ()"), self.tree.showWebPreview)
            QtCore.QObject.connect(self.tree,QtCore.SIGNAL("viewportEntered ()"), self.tree.timerStop)
        elif self.settings.value("SFLvault-qt4/webpreview").toInt()[0] == QtCore.Qt.Unchecked:
            QtCore.QObject.disconnect(self.tree,QtCore.SIGNAL("entered (const QModelIndex&)"), self.tree.startTimer)
            QtCore.QObject.disconnect(self.tree.timer, QtCore.SIGNAL("timeout ()"), self.tree.showWebPreview)
            QtCore.QObject.disconnect(self.tree,QtCore.SIGNAL("viewportEntered ()"), self.tree.timerStop)

    def setLanguage(self):
        """
            Load language
        """
        if self.settings.value("SFLvault-qt4/language").toString():
            lang = self.settings.value("SFLvault-qt4/language").toString()
            bool = self.translator.load("sflvault-qt4_" + lang, "./i18n", "_", ".qm")
            # If not language loaded, print message
            if not bool:
                print self.tr("Warning : unable to load i18n/sflvault-qt4_" + lang)

            self.app.installTranslator(self.translator)

    def setShortcut(self):
        """
            Set shortcuts
        """
        QtGui.QShortcut(QtGui.QKeySequence(QtCore.Qt.CTRL + QtCore.Qt.Key_I),
                        self, self.showHideFilterShort )
        QtGui.QShortcut(QtGui.QKeySequence(QtCore.Qt.CTRL + QtCore.Qt.Key_F),
                        self, self.searchShort )
        QtGui.QShortcut(QtGui.QKeySequence(QtCore.Qt.CTRL + QtCore.Qt.Key_T),
                        self, self.focusOnTree)

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
            self.tree.setSelection(QtCore.QRect(0, 0, name_column_width, 16), QtGui.QItemSelectionModel.Select)
            # Select first row and second column
            self.tree.setSelection(QtCore.QRect(name_column_width, 0, id_column_width, 16), QtGui.QItemSelectionModel.Select)

    def quickConnection(self):
        """
            Launch connection from shortcut
        """
        ret, ok = QtGui.QInputDialog.getText(self.parent, self.tr("Quick connection"),
                                                 self.tr("Service id or service alias :"),
                                                 QtGui.QLineEdit.Normal)
        if not ok or not ret:
            return False

        # Try to know if id is a integer
        id, bool = ret.toInt()
        if not bool:
            # if is not a integer, then it's a QString
            # check if it's something like s#111
            ret = unicode(ret)
            if ret.startswith("s#"):
                id = ret.split("#")[1]
            if not id:
            # Then it's an alias
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
        itemid = indexId.data(QtCore.Qt.DisplayRole).toString()
        try:
            itemid = int(itemid.split("#")[1])
        except ValueError, e:
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
        itemid = indexId.data(QtCore.Qt.DisplayRole).toString()
        try:
            itemid = int(itemid.split("#")[1])
        except ValueError, e:
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
        servid = indexId.data(QtCore.Qt.DisplayRole).toString()
        servid = int(servid.split("#")[1])
        self.addmachine = EditMachineWidget(None, servid, parent=self)
        self.addmachine.exec_()

    def addService(self, machid=None, servid=None):
        """ Add a new service
        """
        # Get Id colunm
        indexId = self.tree.selectedIndexes()[1]
        index = self.tree.selectedIndexes()[0]
        machid = indexId.data(QtCore.Qt.DisplayRole).toString()
        try:
            machid = int(machid.split("#")[1])
        except ValueError, e:
            return False
        self.addservice = EditServiceWidget(False, machid, parent=self)
        self.addservice.exec_()

    def tunnel(self):
        index = self.tree.selectedIndexes()[0]
        indexId = self.tree.selectedIndexes()[1]
        idserv = indexId.data(QtCore.Qt.DisplayRole).toString()
        idserv = int(idserv.split("#")[1])

        tunnel,bool = QtGui.QInputDialog().getText(
                                    self,
                                    "SSH Tunnel",
                                    "Enter the ssh tunnel (ex: -L 5000:127.0.0.1:3306 )",
                                    QtGui.QLineEdit.Normal,
                                    "",
                                    )
        if not bool or tunnel == "":
            return False
        self.connection(idserv, show_tooltip=False, tunnel=tunnel)

    def addItem(self):
        # Get Id colunm
        indexId = self.tree.selectedIndexes()[1]
        index = self.tree.selectedIndexes()[0]
        itemid = indexId.data(QtCore.Qt.DisplayRole).toString()
        itemid = int(itemid.split("#")[1])
        # Check if seleted item is a service
        if index.parent().parent().isValid():
            print index.parent().data(QtCore.Qt.DisplayRole).toString()
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
