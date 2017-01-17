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

try:
    from setuptools import setup, find_packages
except ImportError:
    from distribute_setup import use_setuptools
    use_setuptools()
    from setuptools import setup, find_packages

import platform

dependencies = [
    "pycrypto",
    "decorator",
]

if platform.system() != 'Windows':
    dependencies += ["urwid>=0.9.8.1", "pexpect>=3.0"]

setup(
    name='SFLvault-client',
    version="0.8.0",
    description='Networked credentials store and authentication manager - Client',
    author='Alexandre Bourget',
    author_email='alexandre.bourget@savoirfairelinux.com',
    url='http://www.sflvault.org',
    license='GPLv3',
    install_requires=dependencies,
    packages=find_packages(),
    namespace_packages=['sflvault'],
    include_package_data=True,
    test_suite='nose.collector',
    package_data={'sflvault': ['i18n/*/LC_MESSAGES/*.mo']},
    #message_extractors = {'sflvault': [
    #        ('**.py', 'python', None),
    #        ('templates/**.mako', 'mako', None),
    #        ('public/**', 'ignore', None)]},
    entry_points="""
    [console_scripts]
    sflvault = sflvault.client.commands:main

    [sflvault.services]
    ssh = sflvault.client.services:ssh
    ssh+pki = sflvault.client.services:ssh_pki
    content = sflvault.client.services:content
    sflvault = sflvault.client.services:sflvault
    vnc = sflvault.client.services:vnc
    mysql = sflvault.client.services:mysql
    psql = sflvault.client.services:postgres
    postgres = sflvault.client.services:postgres
    postgresql = sflvault.client.services:postgres
    su = sflvault.client.services:su
    sudo = sflvault.client.services:sudo

    """,
)
