.. SFLvault documentation master file, created by
   sphinx-quickstart on Sat Oct  3 10:37:06 2009.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.


Welcome to SFLvault!
========================================

.. image:: img/sflvault-logo-tagline.png


SFLvault is a **Networked credentials store and authentication manager** developed and maintained by `Savoir-faire Linux
<http://www.savoirfairelinux.com/>`_.

It has a client/vault (server) architecture allowing encrypted storage and organization of a multitude passwords for different machines and services.

This website contains all the documentation for SFLvault. To keep track of its development please follow us on:

* http://projects.savoirfairelinux.com/projects/sflvault
* http://github.com/savoirfairelinux/sflvault



Download the client
-------------------
Ubuntu until version 12.04
^^^^^^
SFLvault is provided by Savoir-faire Linux's PPA_

.. _PPA: https://help.ubuntu.com/community/Repositories/Ubuntu#Adding_PPAs

First make sure you have the required tools to manage PPAS::

  $ sudo apt-get install python-software-properties

Install the ppa::

  $ sudo add-apt-repository ppa:savoirfairelinux/sflvault

And run::

  $ sudo apt-get update
  $ sudo apt-get install sflvault-client

If you would rather have the Qt client::

  $ sudo apt-get update
  $ sudo apt-get install sflvault-client-qt

Ubuntu version 12.10 and upper
^^^^^^

First install pip::

  $  sudo apt-get install python-pip python-dev build-essential 

And run::

  $  sudo pip install SFlvault-client

Fedora
^^^^^^
Install the repository::

  $ sudo yum install https://yum.savoirfairelinux.com/sflvault/f19/x86_64/sflvault-release-1-1.noarch.rpm
  $ sudo yum install sflvault-client

You can also install the graphical client::

  $ sudo yum install sflvault-client-qt
Other
^^^^^

Install from the Python package index::

  $ pip install SFlvault-client

Install the server
-------------------
:ref:`production-setup`

Contents
========

.. toctree::
   :maxdepth: 2
   :glob:

   features
   install
   architecture
   permissions
   api/api
   client_changelog
   server_changelog





Indices and tables
==================

* :ref:`genindex`
* :ref:`search`

