try:
    from setuptools import setup
except ImportError:
    from distutils.core import setup

setup(
    name='sflvault-client',
    version='2.0.0',
    description='Networked credentials store and authentication manager - Client',
    author='Savoir-faire Linux Inc',
    author_email='info@savoirfairelinux.com',
    url='https://sflvault.org',
    packages=['sflvault'],
    setup_requires=["pytest-runner"],
    tests_require=["pytest"],
)
