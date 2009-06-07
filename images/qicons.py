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


def Qicons(icon_name):
    """
        Return selected icon
    """
    global icons
    return QtGui.QIcon(icons[icon_name])
