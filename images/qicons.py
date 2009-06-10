#!/usr/bin/env python
# -*- coding: UTF-8 -*-

import sys
from PyQt4 import QtCore, QtGui
import re
from PyQt4.QtCore import Qt
import shutil
import os


icons = {}
icons["sflvault_icon"] = "images/sflvault.png"
icons["close_filter_icon"] = "images/dialog-close.png"
icons["customer"] = "images/customer.png"
icons["machine"] = "images/machine.png"
icons["service"] = "images/service.png"
icons["mysql"] = "images/mysql.png"
icons["pgsql"] = "images/pgsql.png"
icons["smb"] = "images/smb.png"
icons["wifi"] = "images/wifi.png"
icons["http"] = "images/http.png"
icons["smtp"] = "images/smtp.png"
icons["pop3"] = "images/pop3.png"
icons["imap"] = "images/imap.png"


def Qicons(icon_name):
    """
        Return selected icon
    """
    global icons
    if not icon_name in icons.keys():
        icon_name = "service"
    return QtGui.QIcon(icons[icon_name])
