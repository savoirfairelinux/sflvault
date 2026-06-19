.. image:: ./docs/logos/sflvault-logo-tagline.png

Welcome to SFLvault |badge|
-------------------
.. |badge| image:: https://api.travis-ci.org/savoirfairelinux/sflvault.png?branch=master
SFLvault is a Networked credentials store and authentication manager.

It has a client/vault (server) architecture allowing to cryptographically store and organise loads of passwords for different machines and services.

Package repositories
--------------------

Ubuntu and Debian
~~~~~~~~~~~~~~~~~

Install the repository signing key and add the APT repository::

    sudo apt-get update
    sudo apt-get install -y ca-certificates curl gnupg
    curl -fsSL https://gpl.savoirfairelinux.net/sflvault/sflvault-repo.gpg.key \
        | sudo gpg --dearmor -o /usr/share/keyrings/sflvault-archive-keyring.gpg

For Ubuntu 24.04 LTS (noble)::

    echo "deb [signed-by=/usr/share/keyrings/sflvault-archive-keyring.gpg] https://gpl.savoirfairelinux.net/sflvault noble main" \
        | sudo tee /etc/apt/sources.list.d/sflvault.list

For Ubuntu 26.04 LTS (resolute)::

    echo "deb [signed-by=/usr/share/keyrings/sflvault-archive-keyring.gpg] https://gpl.savoirfairelinux.net/sflvault resolute main" \
        | sudo tee /etc/apt/sources.list.d/sflvault.list

Debian users can use the compatible Ubuntu suite for their environment.

Then install the desired package::

    sudo apt-get update
    sudo apt-get install python3-sflvault-client
    # Optional:
    sudo apt-get install python3-sflvault-client-qt
    sudo apt-get install python3-sflvault-server

Fedora
~~~~~~

Add the DNF repository and install the desired package::

    sudo curl -fsSL -o /etc/yum.repos.d/sflvault.repo https://gpl.savoirfairelinux.net/sflvault/fedora/sflvault.repo
    sudo rpm --import https://gpl.savoirfairelinux.net/sflvault/fedora/RPM-GPG-KEY-sflvault
    sudo dnf makecache
    sudo dnf install python3-sflvault-client
    # Optional:
    sudo dnf install python3-sflvault-client-qt
    sudo dnf install python3-sflvault-server

Contributions
-------------
If you are interested in contributing to this project, feel free to fork this repository.
