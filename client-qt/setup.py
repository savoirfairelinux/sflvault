# -=- encoding: utf-8 -=-
#
# SFLvault - Secure networked password store and credentials manager.
#
# Copyright (C) 2014 Savoir-faire Linux inc.
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

from setuptools import setup, find_packages

import glob

requires = [
    "sflvault-client"
]

setup(
    name               = "sflvault-client-qt",
    version            = "0.8.0",
    description        = "Networked credentials store and authentication manager - Qt Client",
    author             = "Thibault Cohen",
    author_email       = "thibault.cohen@savoirfairelinux.com",
    url                = "http://www.sflvault.org",
    license            = "GPLv3",
    packages           = find_packages(),
    install_requires   = requires,
    namespace_packages = ["sflvault"],
    test_suite         = "nose.collector",
    entry_points       = """
        [console_scripts]
        sflvault-client-qt = sflvault.clientqt:main
    """,
    data_files         = [
        # For the moment, /usr/share/pyshared/sflvault/clientqt is hardcoded before finding a solution
        ("/usr/share/pyshared/sflvault/clientqt/images",          glob.glob("sflvault/clientqt/images/*png")),
        ("/usr/share/pyshared/sflvault/clientqt/images/services", glob.glob("sflvault/clientqt/images/services/*png")),
        ("/usr/share/pyshared/sflvault/clientqt/i18n",            glob.glob("sflvault/clientqt/i18n/*qm"))
	]
)
