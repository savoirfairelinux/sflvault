try:
    from setuptools import setup, find_packages
except ImportError:
    from ez_setup import use_setuptools
    use_setuptools()
    from setuptools import setup, find_packages



setup(
    name='SFLvault-plugin-demo',
    version="0.7.4",
    description='Networked credentials store and authentication manager - Demo plugin',
    author='Alexandre Bourget',
    author_email='alexandre.bourget@savoirfairelinux.com',
    url='http://www.sflvault.org',
    license='GPLv3',
    install_requires=["SFLvault-client"],
    packages=find_packages(exclude=['ez_setup']),
    include_package_data=True,
    entry_points="""
    [sflvault.services]
    demo = sflvault.plugins.demo:demo
    """,
)
