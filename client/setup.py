try:
    from setuptools import setup, find_packages
except ImportError:
    from distribute_setup import use_setuptools
    use_setuptools()
    from setuptools import setup, find_packages

import platform


setup(
    name='SFLvault-client',
    version="0.7.8.1",
    description='Networked credentials store and authentication manager - Client',
    author='Alexandre Bourget',
    author_email='alexandre.bourget@savoirfairelinux.com',
    url='http://www.sflvault.org',
    license='GPLv3',
    install_requires=["SFLvault-common==0.7.8.1",
                      "pycrypto",
                      "decorator",
                      ] + \
                     ([] if platform.system() == 'Windows'
                         else ["urwid>=0.9.8.1",
                               "pexpect>=2.3"]),
    packages=find_packages(exclude=['ez_setup']),
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


