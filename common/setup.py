# -=- encoding: utf-8 -=-
#
# SFLvault - Secure networked password store and credentials manager.
#
# Copyright (C) 2008-2021  Savoir-faire Linux inc.
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

try:
    from setuptools import setup, find_packages
except ImportError:
    from distribute_setup import use_setuptools
    use_setuptools()
    from setuptools import setup, find_packages

requires = [
    'pycrypto',
]

setup(
    name='SFLvault-common',
    version="0.9.0",
    description='Networked credentials store and authentication manager - Common',
    author='Savoir-faire Linux',
    author_email='contact@savoirfairelinux.com',
    url='https://www.sflvault.org',
    license='GPLv3',
    install_requires=requires,
    packages=find_packages(),
    namespace_packages=['sflvault'],
    test_suite='nose.collector',
    entry_points=""" """,
)


