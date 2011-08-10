#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
#    sflvault_qt/docs/infodock.py
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
from sflvault.client import SFLvaultClient
import shutil
import os

from sflvault.clientqt.lib.auth import *


class InfoDock(QtGui.QDockWidget):
    def __init__(self, parent=None ):
        QtGui.QDockWidget.__init__(self, parent)
        self.parent = parent
        self.info = Info(self)
        self.setWidget(self.info)
        self.setWindowTitle(self.tr("Informations"))

        ## Check visibility
        QtCore.QObject.connect(self, QtCore.SIGNAL("visibilityChanged (bool)"), self.parent.menubar.checkDockBoxes)

    def showInformations(self, customerid, machineid=None, serviceid=None):
        """
            Show services informations
        """
        # Save item ids
        self.customerid = customerid
        self.machineid = machineid
        self.serviceid = serviceid
        # Set New object
        self.customer = None
        self.machine = None
        self.service = None
        # Set a new model
#        self.info.model.clear()
#        self.info.model.setHeaders()

        self.customer = getCustomer(customerid)
        self.setWindowTitle("Customer info")
        if machineid and self.customer:
            self.machine = getMachine(machineid)
            self.setWindowTitle("Machine info")
            if self.machine and serviceid:
                self.service = getService(serviceid, True)
                self.setWindowTitle("Service info")
                if not self.service:
                    self.setWindowTitle("Informations")
                    return None
            elif not self.machine:
                self.setWindowTitle("Informations")
                return None
        elif not self.customer:
            self.setWindowTitle("Informations")
            return None
        #self.info.model.attributes = []
        #self.info.edit_info_bar.hide()
        #self.info.save.hide()
        #self.info.reinit.hide()
        #self.info.model.showEditableInformations(self.customer, self.machine, self.service)
        self.info.showInformations(self.customer, self.machine, self.service)


class Info(QtGui.QWidget):
    def __init__(self, parent=None):
        QtGui.QWidget.__init__(self, parent)
        self.parent = parent

        self.service_list = []
        self.machine_list = []
        self.customer_list = []
        self.vault_list = []
        self.service_list_title = []
        self.machine_list_title = []
        self.customer_list_title = []
        self.vault_list_title = []

        # Service info
        service_layout = QtGui.QGridLayout()
        service_layout.setSpacing(False)
        self.service_access_label = QtGui.QLabel(self.tr("Service access"))
        self.service_access = QtGui.QLabel()
        self.service_list_title.append(self.service_access_label)
        self.service_list.append(self.service_access)
        self.service_id_label = QtGui.QLabel(self.tr("Service id"))
        self.service_id = QtGui.QLabel()
        self.service_list_title.append(self.service_id_label)
        self.service_list.append(self.service_id)
        self.service_scheme_label = QtGui.QLabel(self.tr("Service scheme"))
        self.service_scheme = QtGui.QLabel()
        self.service_list_title.append(self.service_scheme_label)
        self.service_list.append(self.service_scheme)
        self.service_host_label = QtGui.QLabel(self.tr("Service host"))
        self.service_host = QtGui.QLabel()
        self.service_list_title.append(self.service_host_label)
        self.service_list.append(self.service_host)
        self.service_port_label = QtGui.QLabel(self.tr("Service port"))
        self.service_port = QtGui.QLabel()
        self.service_list_title.append(self.service_port_label)
        self.service_list.append(self.service_port)
        self.service_username_label = QtGui.QLabel(self.tr("Service username"))
        self.service_username = QtGui.QLabel()
        self.service_list_title.append(self.service_username_label)
        self.service_list.append(self.service_username)
        self.service_params_label = QtGui.QLabel(self.tr("Service path"))
        self.service_params = QtGui.QLabel()
        self.service_list_title.append(self.service_params_label)
        self.service_list.append(self.service_params)
        self.service_url_label = QtGui.QLabel(self.tr("Service url"))
        self.service_url = QtGui.QLabel()
        self.service_list_title.append(self.service_url_label)
        self.service_list.append(self.service_url)
        self.service_parent_label = QtGui.QLabel(self.tr("Service parent"))
        self.service_parent = QtGui.QLabel()
        self.service_list_title.append(self.service_parent_label)
        self.service_list.append(self.service_parent)
        self.service_groups_label = QtGui.QLabel(self.tr("Service group"))
        self.service_groups = QtGui.QLabel()
        self.service_list_title.append(self.service_groups_label)
        self.service_list.append(self.service_groups)
        service_layout.addWidget(self.service_access_label, 0, 0)
        service_layout.addWidget(self.service_access, 0, 1)
        service_layout.addWidget(self.service_id_label, 1, 0)
        service_layout.addWidget(self.service_id, 1, 1)
        service_layout.addWidget(self.service_scheme_label, 2, 0)
        service_layout.addWidget(self.service_scheme, 2, 1)
        service_layout.addWidget(self.service_host_label, 3, 0)
        service_layout.addWidget(self.service_host, 3, 1)
        service_layout.addWidget(self.service_port_label, 4, 0)
        service_layout.addWidget(self.service_port, 4, 1)
        service_layout.addWidget(self.service_username_label, 5, 0)
        service_layout.addWidget(self.service_username, 5, 1)
        service_layout.addWidget(self.service_params_label, 6, 0)
        service_layout.addWidget(self.service_params, 6, 1)
        service_layout.addWidget(self.service_url_label, 7, 0)
        service_layout.addWidget(self.service_url, 7, 1)
        service_layout.addWidget(self.service_parent_label, 8, 0)
        service_layout.addWidget(self.service_parent, 8, 1)
        service_layout.addWidget(self.service_groups_label, 9, 0)
        service_layout.addWidget(self.service_groups, 9, 1)
        self.service_groupbox = QtGui.QGroupBox()
        self.service_groupbox.setTitle(self.tr("Service"))
        self.service_groupbox.setLayout(service_layout)

        # Machine info
        machine_layout = QtGui.QGridLayout()
        machine_layout.setSpacing(False)
        self.machine_id_label = QtGui.QLabel(self.tr("Machine id"))
        self.machine_id = QtGui.QLabel()
        self.machine_list_title.append(self.machine_id_label)
        self.machine_list.append(self.machine_id)
        self.machine_fqdn_label = QtGui.QLabel(self.tr("Machine FQDN"))
        self.machine_fqdn = QtGui.QLabel()
        self.machine_list_title.append(self.machine_fqdn_label)
        self.machine_list.append(self.machine_fqdn)
        self.machine_ip_label = QtGui.QLabel(self.tr("Machine IP"))
        self.machine_ip = QtGui.QLabel()
        self.machine_list_title.append(self.machine_ip_label)
        self.machine_list.append(self.machine_ip)
        self.machine_location_label = QtGui.QLabel(self.tr("Machine Location"))
        self.machine_location = QtGui.QLabel()
        self.machine_list_title.append(self.machine_location_label)
        self.machine_list.append(self.machine_location)
        self.machine_name_label = QtGui.QLabel(self.tr("Machine Name")) 
        self.machine_name = QtGui.QLabel()
        self.machine_list_title.append(self.machine_name_label)
        self.machine_list.append(self.machine_name)
        self.machine_notes_label = QtGui.QLabel(self.tr("Machine Notes"))
        self.machine_notes = QtGui.QLabel()
        self.machine_list_title.append(self.machine_notes_label)
        self.machine_list.append(self.machine_notes)
        machine_layout.addWidget(self.machine_id_label, 0, 0)
        machine_layout.addWidget(self.machine_id, 0, 1)
        machine_layout.addWidget(self.machine_fqdn_label, 1, 0)
        machine_layout.addWidget(self.machine_fqdn, 1, 1)
        machine_layout.addWidget(self.machine_ip_label, 2, 0)
        machine_layout.addWidget(self.machine_ip, 2, 1)
        machine_layout.addWidget(self.machine_location_label, 3, 0)
        machine_layout.addWidget(self.machine_location, 3, 1)
        machine_layout.addWidget(self.machine_name_label, 4, 0)
        machine_layout.addWidget(self.machine_name, 4, 1)
        machine_layout.addWidget(self.machine_notes_label, 5, 0)
        machine_layout.addWidget(self.machine_notes, 5, 1)
        self.machine_groupbox = QtGui.QGroupBox()
        self.machine_groupbox.setTitle(self.tr("Machine"))
        self.machine_groupbox.setLayout(machine_layout)

        # Customer info
        customer_layout = QtGui.QGridLayout()
        customer_layout.setSpacing(False)
        self.customer_id_label = QtGui.QLabel(self.tr("Customer id"))
        self.customer_id = QtGui.QLabel()
        self.customer_list_title.append(self.customer_id_label)
        self.customer_list.append(self.customer_id)
        self.customer_name_label = QtGui.QLabel(self.tr("Customer name"))
        self.customer_name = QtGui.QLabel()
        self.customer_list_title.append(self.customer_name_label)
        self.customer_list.append(self.customer_name)
        customer_layout.addWidget(self.customer_id_label, 0, 0)
        customer_layout.addWidget(self.customer_id, 0, 1)
        customer_layout.addWidget(self.customer_name_label, 1, 0)
        customer_layout.addWidget(self.customer_name, 1, 1)
        self.customer_groupbox = QtGui.QGroupBox()
        self.customer_groupbox.setTitle(self.tr("Customer"))
        self.customer_groupbox.setLayout(customer_layout)

        # Vault info
        vault_layout = QtGui.QGridLayout()
        vault_layout.setSpacing(False)
        self.vault_server_label = QtGui.QLabel(self.tr("Vault address"))
        self.vault_server = QtGui.QLabel()
        self.vault_list_title.append(self.vault_server_label)
        self.vault_list.append(self.vault_server)
        self.vault_user_label = QtGui.QLabel(self.tr("Vault username"))
        self.vault_user = QtGui.QLabel()
        self.vault_list_title.append(self.vault_user_label)
        self.vault_list.append(self.vault_user)
        vault_layout.addWidget(self.vault_server_label, 0, 0)
        vault_layout.addWidget(self.vault_server, 0, 1)
        vault_layout.addWidget(self.vault_user_label, 1, 0)
        vault_layout.addWidget(self.vault_user, 1, 1)
        self.vault_groupbox = QtGui.QGroupBox()
        self.vault_groupbox.setTitle(self.tr("Vault"))
        self.vault_groupbox.setLayout(vault_layout)

        # QGridLayout
        mainLayout = QtGui.QGridLayout()
        mainLayout.addWidget(self.service_groupbox, 0, 0)
        mainLayout.addWidget(self.machine_groupbox, 1, 0)
        mainLayout.addWidget(self.customer_groupbox, 2, 0)
        mainLayout.addWidget(self.vault_groupbox, 3, 0)

        # Geometries
        self.setWindowTitle(self.tr("Items Informations"))

        self.show_vault_info()
        self.service_groupbox.hide()
        self.machine_groupbox.hide()
        self.customer_groupbox.hide()

        #TODO
        # Fix column width
        # change cursor to selectable
        # add marquee qlabel when text is too long
        for info in self.service_list_title:
            info.setMinimumWidth(130)
            info.setMinimumHeight(20)

        for info in self.machine_list_title:
            info.setMinimumWidth(130)
            info.setMinimumHeight(20)

        for info in self.customer_list_title:
            info.setMinimumWidth(130)
            info.setMinimumHeight(20)

        for info in self.vault_list_title:
            info.setMinimumWidth(130)
            info.setMinimumHeight(20)

        for info in self.service_list:
            info.setTextInteractionFlags(Qt.TextSelectableByMouse)
            info.setAlignment(QtCore.Qt.AlignRight)
            info.setMargin(2)
            info.setMinimumHeight(20)
            info.setWordWrap(1)

        for info in self.machine_list:
            info.setTextInteractionFlags(Qt.TextSelectableByMouse)
            info.setAlignment(QtCore.Qt.AlignRight)
            info.setMargin(2)
            info.setMinimumHeight(20)
            info.setWordWrap(1)

        for info in self.customer_list:
            info.setTextInteractionFlags(Qt.TextSelectableByMouse)
            info.setAlignment(QtCore.Qt.AlignRight)
            info.setMargin(2)
            info.setMinimumHeight(20)
            info.setWordWrap(1)

        for info in self.vault_list:
            info.setTextInteractionFlags(Qt.TextSelectableByMouse)
            info.setAlignment(QtCore.Qt.AlignRight)
            info.setMargin(2)
            info.setMinimumHeight(20)
            info.setWordWrap(1)

        #self.service_url.setTextInteractionFlags(Qt.TextSelectableByMouse)

        # Show window
        mainLayout.setAlignment(QtCore.Qt.AlignTop)
        self.setLayout(mainLayout)

    def show_service_info(self, service):
        if not 'group_id' in service or service['group_id'] == '':
            self.service_access.setText(self.tr(u"""<font color="red"><b>\
                                                 Denied</b></font>"""))
        else:
            self.service_access.setText(self.tr(u"""<font color="green"><b>\
                                                 Authorized</b></font>"""))

        self.service_id.setText(u"<b>s#" + unicode(service['id']) + u"</b>")

        advanced_url = unicode(service['url'])
        # Split data
        if len(advanced_url.split("@")) > 2:
            temp = advanced_url.rsplit("@",1)
            username = temp[0].split("://")[-1]
            protocol = temp[0].split("://")[0]
            url = temp[1]
            url = QtCore.QUrl(protocol + "://" + url)
        else:
            url = QtCore.QUrl(advanced_url)
        username = unicode(url.userName())
        protocol = unicode(url.scheme())
        port = unicode(url.port() if url.port() > 0 else '')
        host = unicode(url.host())
        uri = unicode(url.path())
        # Set fields
        self.service_username.setText(username)
        self.service_host.setText(host)
        self.service_port.setText(port)
        self.service_scheme.setText(protocol)
        self.service_params.setText(uri)

        url.setUserName('')
        self.service_url.setText(url.toString())

        if service['parent_service_id'] != 0 \
           and service['parent_service_id'] is not None:
            self.service_parent.setText(u"<b>s#" + \
                        unicode(service['parent_service_id']) + u"</b>")
        else:
            self.service_parent.clear()

        groups_list = "<br>".join([u"g#%s - %s" % tuple(group )
                                   for group in service['groups_list']])
            
        self.service_groups.setText(groups_list)

    def show_machine_info(self, machine):
        self.machine_id.setText(u"<b>m#" + unicode(machine['id']) + u"</b>")
        self.machine_fqdn.setText(machine['fqdn'])
        self.machine_ip.setText(machine['ip'])
        self.machine_location.setText(machine['location'])
        self.machine_name.setText(machine['name'])
        self.machine_notes.setText(machine['notes'])

    def show_customer_info(self, customer):
        self.customer_id.setText(u"<b>c#" + unicode(customer['id']) + u"</b>")
        self.customer_name.setText(unicode(customer['name']))

    def show_vault_info(self):
        settings = self.parent.parent.settings
        self.vault_server.setText(settings.value("SFLvault/url").toString())
        self.vault_user.setText(settings.value("SFLvault/username").toString())

    def showInformations(self, customer, machine=None, service=None):
        if service \
           and 'customer' in customer \
           and 'machine' in machine \
           and 'services' in service:
            # Show service, machine and customer
            self.service_groupbox.show()
            self.machine_groupbox.show()
            self.customer_groupbox.show()
            self.show_service_info(service['services'][-1])
            self.show_machine_info(machine['machine'])
            self.show_customer_info(customer['customer'])
        elif machine \
           and 'customer' in customer \
           and 'machine' in machine:
            # Hide service and machine, show customer
            self.service_groupbox.hide()
            self.machine_groupbox.show()
            self.customer_groupbox.show()
            self.show_machine_info(machine['machine'])
            self.show_customer_info(customer['customer'])
        elif customer \
           and 'customer' in customer:
            # Hide all
            self.service_groupbox.hide()
            self.machine_groupbox.hide()
            self.customer_groupbox.show()
            self.show_customer_info(customer['customer'])
        else:
            self.service_groupbox.hide()
            self.machine_groupbox.hide()
            self.customer_groupbox.hide()

