try:
    from setuptools import setup, find_packages
except ImportError:
    from distribute_setup import use_setuptools
    use_setuptools()
    from setuptools import setup, find_packages


setup(
    name='SFLvault-common',
    version="0.7.8.1",
    description='Networked credentials store and authentication manager - Common',
    author='Alexandre Bourget',
    author_email='alexandre.bourget@savoirfairelinux.com',
    url='http://www.sflvault.org',
    license='GPLv3',
    install_requires=["pycrypto",
                      ],
    packages=find_packages(exclude=['ez_setup']),
    test_suite='nose.collector',
    entry_points=""" """,
)


