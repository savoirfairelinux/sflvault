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

import os
import sys

from setuptools import setup, find_packages

here = os.path.abspath(os.path.dirname(__file__))
README = open(os.path.join(here, 'README.txt')).read()
CHANGES = open(os.path.join(here, 'CHANGES.txt')).read()

requires = [
    'SFLvault-client',
    'SQLAlchemy',
    'venusian',
    'zope.sqlalchemy',
    'decorator',
    'pyOpenSSL',
]

setup(
    name='SFLvault-server',
    version='0.8.0.0',
    description='Networked credentials store and authentification manager - Server',
    author='Alexandre Bourget',
    author_email='alexandre.bourget@savoirfairelinux.com',
    url='http://www.sflvault.org',
    long_description=README + '\n\n' + CHANGES,
    classifiers=[
        "Programming Language :: Python",
        "Topic :: Internet :: WWW/HTTP",
    ],
    packages=find_packages(),
    namespace_packages=['sflvault'],
    include_package_data=True,
    zip_safe=False,
    package_data={'sflvault': ['i18n/*/LC_MESSAGES/*.mo']},
    test_suite='sflvault',
    install_requires=requires,
)
