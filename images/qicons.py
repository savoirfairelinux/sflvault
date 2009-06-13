#!/usr/bin/env python
# -*- coding: UTF-8 -*-

import sys
from PyQt4 import QtCore, QtGui
import re
from PyQt4.QtCore import Qt
import shutil
import os

# Set folders
image_folder = "images/"
image_service_folder = image_folder + "services/"

# load standard icons
icons = {}
icons["sflvault_icon"] = "images/sflvault.png"
icons["close_filter_icon"] = "images/dialog-close.png"
icons["customer"] = "images/customer.png"
icons["machine"] = "images/machine.png"
icons["critical"] = "images/critical.png"
icons["warning"] = "images/warning.png"
icons["information"] = "images/information.png"

# Auto load all service icons in images/services/ folder
service_icons = {}
service_icons["service"] = "images/service.png"
for file in os.listdir("images/services"):
    service, ext = os.path.splitext(file)
    if ext in [".jpg", ".jpeg", ".png"]:
        service_icons[service] = image_service_folder + service + ".png"


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
        return QtGui.QIcon(service_icons[icon_name])
    # Return standard icons
    else:
        return QtGui.QIcon(icons[icon_name])
