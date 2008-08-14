try:
    from setuptools import setup, find_packages
except ImportError:
    from ez_setup import use_setuptools
    use_setuptools()
    from setuptools import setup, find_packages



setup(
    name='SFLvault',
    version="0.5.0",
    description='Secure networked password store and credentials manager - Bundle',
    author='Alexandre Bourget',
    author_email='alexandre.bourget@savoirfairelinux.com',
    url='http://www.sflvault.org',
    license='GPLv3',
    install_requires=["Pylons>=0.9.6.1",
                      "SQLAlchemy>=0.4",
                      "pycrypto",
                      "pysqlite",
                      #"SFLvault_common>=0.5.0",
                      ],
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

    """,
)





#setup(
#    name='SFLvault-common',
#    version="0.5.0",
#    description='Secure networked password store and credentials manager - Common libs',
#    author='Alexandre Bourget',
#    author_email='alexandre.bourget@savoirfairelinux.com',
#    url='http://www.sflvault.org',
#    install_requires=["pycrypto"],
#    packages=['sflvault.lib.common'],  #find_packages(exclude=['ez_setup']),
#    include_package_data=True,
#    test_suite='nose.collector',
#    #package_data={'sflvault': ['i18n/*/LC_MESSAGES/*.mo']},
#    #message_extractors = {'sflvault': [
#    #        ('**.py', 'python', None),
#    #        ('templates/**.mako', 'mako', None),
#    #        ('public/**', 'ignore', None)]},
#    entry_points="",
#    #[paste.app_factory]
#    #main = sflvault.config.middleware:make_app
#    #
#    #[paste.app_install]
#    #main = pylons.util:PylonsInstaller
#    #
#    #[console_scripts]
#    #sflvault = sflvault.client:main
#)



#setup(
#    name='SFLvault-client',
#    version="0.5.0",
#    description='Secure networked password store and credentials manager - Client',
#    author='Alexandre Bourget',
#    author_email='alexandre.bourget@savoirfairelinux.com',
#    url='http://www.sflvault.org',
#    install_requires=["pycrypto",
#                      #"SFLvault_common>=0.5.0",
#                      ],
#    packages=['sflvault.client'],  # find_packages(exclude=['ez_setup']),
#    include_package_data=True,
#    test_suite='nose.collector',
#    package_data={'sflvault': ['i18n/*/LC_MESSAGES/*.mo']},
#    #message_extractors = {'sflvault': [
#    #        ('**.py', 'python', None),
#    #        ('templates/**.mako', 'mako', None),
#    #        ('public/**', 'ignore', None)]},
#    entry_points="""
#    [console_scripts]
#    sflvault = sflvault.client.client:main
#    """,
#)
