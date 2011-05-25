try:
    from setuptools import setup, find_packages
except ImportError:
    from distribute_setup import use_setuptools
    use_setuptools()
    from setuptools import setup, find_packages



setup(
    name='SFLvault-server',
    version="0.7.8.1",
    description='Networked credentials store and authentication manager - Server',
    author='Alexandre Bourget',
    author_email='alexandre.bourget@savoirfairelinux.com',
    url='http://www.sflvault.org',
    license='GPLv3',
    install_requires=["Pylons==0.9.7",
                      "SQLAlchemy==0.5.8",
                      "pysqlite",
                      "simplejson",
                      "SFLvault-common==0.7.8.1",
                      "Routes==1.10.3",
                      "Paste==1.7.3.1",
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
    """,
)


