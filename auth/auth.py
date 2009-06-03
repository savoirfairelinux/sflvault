# -*- coding: UTF-8 -*-

import sys
from PyQt4 import QtCore, QtGui
from sflvault.client import SFLvaultClient

token = None

def getAuth():
    """
        Get authentication
    """
    global token
    if not token:
        token = SFLvaultClient()
        token.search("[a]")
    return token
    

