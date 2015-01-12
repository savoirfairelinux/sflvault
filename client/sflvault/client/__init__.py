# -=- encoding: utf-8 -=-
#
# SFLvault - Secure networked password store and credentials manager.
#
# Copyright (C) 2008-2009  Savoir-faire Linux inc.
#
# Author: Alexandre Bourget <alexandre.bourget@savoirfairelinux.com>
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

import os

if '1' == os.environ.get('SFLVAULT_SSL_WORKAROUND_BAD_SERVER_CERTIFICATE'):
    import sys
    if sys.version_info[:3] < (2, 7, 9):
        import warnings
        warnings.warn('The SFLVAULT_SSL_WORKAROUND_BAD_SERVER_CERTIFICATE '
                      'environment parameter is only usable in 2.7.9 and higher.')
    else:
        import ssl
        if sys.version_info[0] >= 3:
            from http.client import HTTPSConnection as orig
        else:
            from httplib import HTTPSConnection as orig

        class HTTPSConnection(orig, object):
            def __init__(self, *args, **kwargs):
                if sys.version_info[:2] < (3, 4):
                    kwargs['strict'] = False
                kwargs['context'] = ssl._create_unverified_context()
                super(HTTPSConnection, self).__init__(*args, **kwargs)


from sflvault.client.commands import SFLvaultCommand
from sflvault.client.commands import SFLvaultShell
from sflvault.client.client import SFLvaultClient

