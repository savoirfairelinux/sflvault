try:
    from setuptools import setup, find_packages
except ImportError:
    from ez_setup import use_setuptools
    use_setuptools()
    from setuptools import setup, find_packages



setup(
    name='SFLvault',
    version="0.7.2.1",
    description='Networked credentials store and authentication manager',
    author='Alexandre Bourget',
    author_email='alexandre.bourget@savoirfairelinux.com',
    url='http://www.sflvault.org',
    license='GPLv3',
    install_requires=["Pylons>=0.9.7rc4",
                      "SQLAlchemy<=0.4.9999",
                      "pycrypto",
                      "pysqlite",
                      "pexpect>=2.3",
                      "urwid>=0.9.8.1",
                      "ipython"
                      ],
    # For server installation:
    #  "ipython"
    #  "pysqlite"
    # For development installation:
    #  "nosexml"
    #  "elementtree"
    #  "coverage"
    packages=find_packages(exclude=['ez_setup']),
    include_package_data=True,
    test_suite='nose.collector',
    package_data={'sflvault': ['i18n/*/LC_MESSAGES/*.mo']},
    #message_extractors = {'sflvault': [
    #        ('**.py', 'python', None),
    #        ('templates/**.mako', 'mako', None),
    #        ('public/**', 'ignore', None)]},
    entry_points="""
    [paste.app_factory]
    main = sflvault.config.middleware:make_app

    [paste.app_install]
    main = pylons.util:PylonsInstaller

    [console_scripts]
    sflvault = sflvault.client.client:main

    [sflvault.services]
    ssh = sflvault.client.services:ssh
    vnc = sflvault.client.services:vnc
    mysql = sflvault.client.services:mysql
    su = sflvault.client.services:su
    sudo = sflvault.client.services:sudo

    """,
)


