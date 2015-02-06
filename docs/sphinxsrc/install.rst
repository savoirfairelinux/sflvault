=========================
Installation instructions
=========================

.. warning::

    Before you start, you should install the client on some computer from where you're going to connect to the SFLvault server. This is because the client must be ready for when the server is setup: you have 15 minutes to set up the admin account after a certain point.


.. _production-setup:

----------------
Production setup
----------------

Installing from your distribution's package manager
===================================================

This section will be added soon. In the meantime the preferred way to install SFLvault is from PyPI.

Installing from PyPI
====================

.. warning::

   The instructions in this wiki are for the latest version of SFLvault (0.8) that has not yet been released on the Python package index. It will be updated shortly. In the meantime please refer to:

    https://projects.savoirfairelinux.com/projects/sflvault/wiki/NewServerInstallation   

.. _install-dependencies:

Install system dependencies
---------------------------

.. note::
   These instructions assume you are installing on Ubuntu 10.04 or newer. Specific package manager related commands and package names may vary.

SFLvault requires Python 2.6 or higher.

SFLvault requires the python headers to compile the crypto libraries. These instructions assume
you are installing SFLvault inside a virtual environment.

::

   $ sudo apt-get install python-virtualenv python-pip python-dev autoconf

Make a directory where the application will live::

   $ mkdir SFLvault
   $ cd SFLvault

.. note::

  If you want this installation to become production installation, make sure you create a user and a group for that purpose, and that you issues those commands as that user.

.. _configure-venv:

Configure your virtual environment
----------------------------------

.. code::

   $ virtualenv --distribute env
   $ . env/bin/activate
   (env)$ pip install -r requirements.freeze

.. _client-install::
Client installation first
-------------------------

To properly setup your server (with ``user-setup``), you'll need SFLVault's client installed. It has
the same dependencies as the server, so once you have them, you can install a client with a simple::

  (env)$ pip install SFLVault-client

Install SFLvault
----------------

.. code::

  (env)$ pip install SFLvault-server

.. note::

 If you get some permission denied, make sure you have activated your environment with :code:`. env/bin/activate` (do not forget the dot!)

.. _run-sflvault:

Run SFLvault
------------

At this point it is possible to run SFLvault with the default configuration:

.. code::
   
   python -m sflvault.server

.. warning::
   
   The default configuration does not enable SSL and is therefore insecure. It is recommended to generate a SSL key and certificate and configure SFLvault to use it. The following configuration file provides instructions to configure SSL on your installation.

To provide a configuration file to your SFLvault instance, please use the following file. Options are detailed in the :ref:`configuration-file` section.

.. code::

   #
   # SFLvault - Pylons development environment configuration
   #
   # The %(here)s variable will be replaced with the parent directory of this file
   #
   [sflvault]
   sflvault.vault.session_timeout = 90
   sflvault.vault.setup_timeout = 300
   sflvault.vault.session_trust = true
   sqlalchemy.url = sqlite:///%(here)s/sflvault.sqlite
   sflvault.keyfile = /path/to/ssl/keyfile
   sflvault.certfile = /path/to/ssl/certfile

   # BEGIN SSL note:

   # sflvault.allow-unverified-ssl-context = 1

   # If you happen to use a self-signed server certificate and you have Python >= 2.7.9
   # then you'll need to enable this option.
   # END SSL note.

   # Logging configuration
   [loggers]
   keys = root, sflvault, sqlalchemy
   
   [handlers]
   keys = console
   
   [formatters]
   keys = generic
   
   [logger_root]
   level = INFO
   handlers = console

   [logger_sflvault]
   level = DEBUG
   handlers = console
   qualname = sflvault
   
   # SQLAlchemy logging from within paster shell
   [logger_sqlalchemy]
   # INFO or DEBUG for all SQL statements.
   level = INFO
   handlers =
   qualname = sqlalchemy.engine

   [handler_console]
   class = StreamHandler
   args = (sys.stderr,)
   level = NOTSET
   formatter = generic
   
   [formatter_generic]
   format = %(asctime)s,%(msecs)03d %(levelname)-5.5s [%(name)s] %(message)s
   datefmt = %H:%M:%S

sflvault.keyfile and sflvault.certfile are the paths to your keyfile and certfile. You can use OpenSSl to generate these:

.. code::

   openssl req -x509 -newkey rsa:2048 -keyout key.pem -out cert.pem -days XXX


Once you have created your configuration file, you can run tell SFLvault to use it by calling the following: 

.. code::

   python -m sflvault.server /path/to/config

The first time you run the server, it will initialize a new database with a new 'admin' user. From this moment, you have 15 minutes to setup your admin account.

.. _create-admin-account:

Create the admin account
------------------------

.. warning::

  If you're too late, and you notice that you've expired the timer, don't worry! Please go to :ref:`recreating-admin-account`


On your other computer (or on the same), run:

.. code ::

   $ sflvault user-setup admin https://localhost:5000/vault/rpc

This will generate a new keypair, and store the public key in the vault. The admin account is setup, and you may start using the vault.


You should see something like:

.. code::

   ...
   Enter passphrase (to secure your private key):
   Enter passphrase again:
   Vault says: User setup complete for admin
   Saving settings...

Congratulations! You now have running instance of SFLvault! For information on how to use it, please refer to the :doc:`user manual </usermanual>`.



-----------------
Development setup
-----------------

Installing from source
======================

Get the latest version from git::

  $ git clone http://git.sflvault.org/sflvault.git SFLvault

This will create a SFLvault directory where the application will live.

Before continuing, make sure to :ref:`install-dependencies` and :ref:`configure-venv`

You can now install the required SFLvault packages::

  $ cd common
  $ python setup.py develop
  $ cd ../server
  $ python setup.py develop
  $ cd ../client
  $ python setup.py develop

At this point you can :ref:`run-sflvault` and :ref:`create-admin-account`!

Run the tests
-------------
You need tox to run the tests:

.. code::

   $ pip install tox

Which will let you run the vault's test suite:

.. code::

   $ tox

----------------------
Additional information
----------------------

Configuration parameters
========================

.. _configuration-file:

Section sflvault
----------------

*sflvault.host*
  The address at which we host the server. ``localhost`` is the default and results in a local-only
  server. If you want to serve externally, you can set this to ``0.0.0.0``.

*sflvault.port*
  The port to listen to. Default is ``5000``.

*sflvault.vault.session_timeout*
  Determines how long the user can wait, in seconds,  before issuing two commands to SFLvault. 

  Default value is 60 seconds.

*sflvault.vault.setup_timeout*
  Determines how long a user has, in seconds, to issue a `user-setup` command and configure his
  account after it has been created.

  Default value is 300 seconds.

*sflvault.vault.session_trust*
  Determines if a user's session can be cached and used for login later in time.
  **This parameter is deprecated and will be removed in 0.9.0**

  Default value is false.

*sflvault.keyfile*

*sflvault.certfile*

  Paths to a key file and certificate file to use the SSL mode. When both configurations are set,
  the server is started in SSL mode, otherwise, it's started in plain HTTP mode.

*sflvault.allow-unverified-ssl-context*
  Determines if a user bypass the server certificate verification.
  Which can be useful if your server certificate happens to be self-signed.
  Default value is undefined. Set to '1' to enable the option.

*sqlalchemy.url (default value: sqlite://%(here)s/sflvault.sqlite)*
  Where SFLVault's database is. It's a SQLAlchemy URL, about which you can have more information at
  http://docs.sqlalchemy.org/en/rel_0_8/core/engines.html

Section loggers, handlers and formatters
----------------------------------------
Logging in SFLvault is done with the standard logging module. For further information, please refer to the official python documentation:

 * http://docs.python.org/2/library/logging.html

.. _recreating-admin-account:

Recreating the admin account
============================

If you get an error from the Vault because you waited more than 15 minutes between the ``setup-app`` and the call to ``user-setup``, then you need to start with a new vault:

1. Stop your server.
2. Delete your database.
3. Start your server.

SSL and password safety
=======================

Running the server over SSL is required to ensure password safety. The ``show`` command sends
passwords in an encrypted form, but ``service-add`` and ``service-passwd`` do not. Someone listening
to the communications between the client and the server could very easily get these passwords.

In old Python versions (< 2.7.9), the SSL server certificate wasn't strictly validated.
If you happen to have a self-signed server certificate (or expired) and you run Python >= 2.7.9 then
you can define sflvault.allow-unverified-ssl-context (to '1') in your configuration file to bypass
the certificate strict validation.

Make SFLvault a system service
==============================

To run as a server, you'll need to have an ``eggcache`` directory, so go to where you created the config file:

.. code ::

   $ cd SFLvault
   $ mkdir eggcache

and install this file in ``/etc/init.d/sflvault`` (tweak as needed):

.. code::

   #!/bin/sh -e

   APPDIR="/home/MyUser/SFLvault"
   cd $APPDIR
   export PYTHON_EGG_CACHE="$APPDIR/eggcache"
   PIDFILE="$APPDIR/paster.pid"
   LOGFILE="$APPDIR/paster.log"
   COMMAND="$APPDIR/env/bin/python -m sflvault.server /path/to/configuration --user=MyUser --group=MyUser --pid-file=$PIDFILE --log-file=$LOGFILE"

  case "$1" in
    start)
      $COMMAND start
      ;;
    stop)
      $COMMAND stop
      ;;
    restart)
      $COMMAND restart
      ;;
    *)
      echo $"Usage: $0 {start|stop|restart}"
      exit 1
  esac

  exit 0

Then run:

.. code ::

   chmod +x /etc/init.d/sflvault
