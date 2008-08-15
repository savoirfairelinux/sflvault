# -=- encoding: utf-8 -=-
#
# SFLvault - Secure networked password store and credentials manager.
#
# Copyright (C) 2008  Savoir-faire Linux inc.
#
# Author: Alexandre Bourget <alexandre.bourget@savoirfairelinux.com>
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

"""This file contains the remoting services. Everything that is required
for automated connection to remote hosts, even with multiple hops (e.g.: ssh to
ssh to ssh to http)"""

from sflvault.client.utils import *

__all__ = ['Service', 'Chain']


# Mother class for service handlers.
class Service(object):
    """Object to describe a service (ex: ssh) and check how it is possible
    for it to establish a connection, even through a chain of services (like
    other ssh's, vpns, port-forwards, etc..)

    This class is a mother class to be inherited from all the service-specific
    objects (ssh, vnc, rdp, mysql, http, https, drac, ftp, postgresql, su,
    sudo, etc..)"""

    provides_modes = []     # List what a service handler supports (gives SHELL access
                            # or can provide PORT_FORWARD, etc. Defaults to nothing
                            # special: plugin is always an end-point.

    parent = None  # Used for link-listing
    child = None   # Used for link-listing

    # These two will be set for child operating in THROUGH_FWD_PORT mode
    forward_host = None
    forward_port = None

    # This will be filled for child requiring a `shell` handle
    shell_handle = None

    # This will be assigned when running required()
    provides = None

    # This is set by __init__, from Chain::__init__(). It's a dict. received by
    # XML-RPC mostly..
    data = None

    def __init__(self, data):
        self.data = data
        self.url = urlparse.urlparse(data['url'])

    def set_child(self, child):
        """Set the child of this service (sets the parent on the child too)"""
        self.child = child
        child.parent = self
        
    def unlink_child(self):
        """Unlink parent from child.

        Call on the first parent to unlink all chain"""
        c = self.child
        p = self.parent

        self.child = None
        self.parent = None
        
        if c:
            c.unlink()
        # Not needed (loops in vain) if called from the first parent:
        #if p:
        #    p.unlink()


    def provides(self, mode):
        """Return True of False, whether it supports the provisioning mode"""
        if not mode:
            return True
        else:
            return mode in self.__class__.provides_modes


    # Abstract functions that must exist in childs

    def required(self, mode=None):
        """Called to setup the chain and make dependencies/providings checks"""
        raise NotImplementedError

    def prework(self):
        """Called when Chain::connect() is called on each Service() to setup
        communication for that particular service."""
        raise NotImplementedError
        
    def interact(self):
        """This function will be called only if the last of the chain"""
        raise NotImplementedError
        
    def postwork(self):
        """Called after interact() is finished for the last child, in reverse order."""
        raise NotImplementedError
        


class Chain(object):
    """Service chain handler.

    Usage:

    >>> chain = Chain(services_struct)
    # Setup the chain, make sure everything is fine.
    >>> chain.setup()
    >>> chain.connect()

    services_struct is the structure received from an sflvault.show() XML-RPC
    call."""

    # Link-list of the Service objects, 
    service_list = None
    ready = False

    def __init__(self, services=None):
        """Initialise the Chain object"""
        self.services = services

        
    def setup(self):
        """Tries to set up the service chain (one service at a time).
        
        Raises exceptions if a service can't be handled, or doesn't
        have all the required connection types (ex: no port forward
        exist prior to accessing a service which requires one, just like
        you can't establish an SSH connection over an HTTP connection)."""

        from pkg_resources import iter_entry_points

        # Create Service objects for each of the service in the hierarchy.
        service_list = []
        for srvdata in self.services:
            parsed_url = urlparse.urlparse(srvdata['url'])
            service = None

            for ep in iter_entry_points('sflvault.services'):
                if ep.name == parsed_url.scheme:
                    srvobj = ep.load()
                    service = srvobj(srvdata)
                    break

            if not service:
                raise RemotingException("Service %s has no handler" % srvdata['url'])

            service_list.append(service)
            
        # Link the services as parent/child.
        last = service_list[0]
        for i in range(0, len(service_list) - 1):
            service_list[i].set_child(service_list[i+1])
            last = service_list[i+1]

        self.service_list = service_list
        self.last_service = last

        # Call .required() on the LAST element, and setup all the chain.
        if not last.required():
            raise RemotingException("No services route to destination")
        else:
            self.ready = True
            return True


    def unlink_all(self):
        self.last_service = None
        sl = service_list
        self.service_list = None

        self.service_list[0].unlink_child()
        

    def connect(self):
        """Connect to the servers in cascade, and do whatever is possible
        to handle connectivity of any time (ssh connections, port forwards,
        etc)"""
        if not self.ready:
            raise RemotingException("Chain not ready. Call setup() first.")

        last = None
        
        # Setup communication
        for srv in self.service_list:
            srv.prework()
            last = srv

        # Interact with end-point
        last.interact()

        # Close-up communication
        for srv in reversed(self.service_list):
            srv.postwork()

        print "Chain::connect() done"
