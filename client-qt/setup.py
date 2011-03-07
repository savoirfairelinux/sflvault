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
                    #"PyQt",
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


