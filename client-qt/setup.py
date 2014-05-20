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



setup(
    name='SFLvault-client-qt',
    version="0.7.8.2",
    description='Networked credentials store and authentication manager - Qt Client',
    author='Thibault Cohen',
    author_email='thibault.cohen@savoirfairelinux.com',
    url='http://www.sflvault.org',
    license='GPLv2',
    install_requires=[
        "SFLvault-client==0.7.8.2",
        "SFLvault-common==0.7.8.1",
    ],
    include_package_data=True,
    packages=find_packages(exclude=['ez_setup']),
    test_suite='nose.collector',
    #message_extractors = {'sflvault': [
    #        ('**.py', 'python', None),
    #        ('templates/**.mako', 'mako', None),
    #        ('public/**', 'ignore', None)]},
    entry_points="""
    [console_scripts]
    sflvault-client-qt = sflvault.clientqt:main
    """,
)
