#!/usr/bin/env python
# -*- coding: UTF-8 -*-
#
#    images/qicons.py
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
import shutil
import os

# load standard icons
icons = {}
icons["sflvault_icon"] = os.path.join("images", "sflvault.png")
icons["close"] = os.path.join("images", "close.png")
icons["customer"] = os.path.join("images", "customer.png")
icons["machine"] = os.path.join("images", "machine.png")
icons["critical"] = os.path.join("images", "critical.png")
icons["warning"] = os.path.join("images", "warning.png")
icons["information"] = os.path.join("images", "information.png")

# Auto load all service icons in images/services/ folder
service_icons = {}
service_icons["service"] = os.path.join("images", "service.png")
this_dir = os.path.dirname(os.path.dirname(__file__))
services_dir = os.path.join(this_dir, "images", "services")
for file in os.listdir(services_dir):
    service, ext = os.path.splitext(file)
    if ext in [".jpg", ".jpeg", ".png"]:
        service_icons[service] = os.path.join("images", "services",
                                              service + ext)


def Qicons(icon_name, type=None):
    """
        Return selected icon
    """
    global icons
    global service_icons

    # Get service icons
    if type == "service":
        if not icon_name in service_icons.keys():
            icon_name = "service"
        return QtGui.QIcon(os.path.join(this_dir, service_icons[icon_name]))
    # Return standard icons
    else:
        return QtGui.QIcon(os.path.join(this_dir, icons[icon_name]))
