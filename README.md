# SFLVault

This branch tracks the work in progress on version 2.0 of the SFLVault client.


## Install

Install Pipenv (https://pipenv.readthedocs.io/en/latest/install/#installing-pipenv):
> pip install --user pipenv

Troubleshooting
* Check that ~/.local/bin is in your PATH:
> echo $PATH

If not, append this to your .bashrc:
> export PATH=$PATH:~/.local/bin

Install project's dependencies:
> pipenv install