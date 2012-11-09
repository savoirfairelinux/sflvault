# -=- encoding: utf-8 -=-
#
# SFLvault - Secure networked password store and credentials manager.
#
# Copyright (C) 2008-2009  Savoir-faire Linux inc.
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

from tests import BaseTestCase
from sflvault.common import VaultError
from sflvault.common.crypto import *
from sflvault.client.client import authenticate

import logging

log = logging.getLogger('tester')

class TestVault(BaseTestCase):
    def setUp(self):
        self.vault = self.getVault()

    def test_customer_add(self):
        """testing add a new customer to the vault"""
        res = self.vault.customer_add('Testing Customer 1')
        cid1 = res['customer_id']
        self.assertTrue(cid1, 1)
        self.assertEqual(res['message'], 'Customer added')

    def test_alias_add(self):
        """testing add a new alias to the vault"""
        cres = self.vault.customer_add(u"Testing é les autres")
        alias = "c#%d" % cres['customer_id']
        ares = self.vault.cfg.alias_add("testing_alias", alias)
        self.assertTrue(ares)

    def test_user_add(self):
        """testing add a new user to the vault"""
        ures = self.vault.user_add("test_username")
        self.assertTrue("User added" in ures['message'])
        ures = self.vault.user_add("test_admin", True)
        self.assertTrue("Admin user added" in ures['message'])

    def test_group_add(self):
        """testing add a new group to the vault"""
        gres = self.vault.group_add("test_group")
        self.assertTrue(int(gres['group_id']) > 0)

    def test_group_add_user(self):
        """Adding a user that's already in the group."""
        # I'm already added to that group, by default
        gres1 = self.vault.group_add("test_group1_user")

        try: gares1 = self.vault.group_add_user(gres1['group_id'], 1)
        except VaultError, e: self.assertTrue('already in' in str(e))


    def test_group_add_service(self):
        """testing add a service to a group to the vault & search"""
        gres3 = self.vault.group_add("test_group3_user")
        self.assertFalse(gres3['error'])
        cres = self.vault.customer_add(u"Testing é les autres")
        self.assertTrue('added' in cres['message'])
        self.assertFalse(cres['error'])
        mres = self.vault.machine_add(str(cres['customer_id']), 
                                      u"Machine namé 3",
                                      "domain1.example2.com", 
                                      '4.3.2.1',
                                      None, 
                                      None)
        self.assertFalse(mres['error'])

        # Add service with metadata, as a dictionary
        sres = self.vault.service_add(mres['machine_id'],
                                      None, 
                                      'ssh://root@localhost',
                                      [gres3['group_id']], 
                                      'test_secret',
                                      u'Some notés',
                                      {'meta': 'data'})
        self.assertFalse(sres['error'])
        dres = self.vault.service_del(sres['service_id'])
        self.assertTrue(dres is not None)

        # Test without metadata
        sres = self.vault.service_add(mres['machine_id'],
                                      None, 
                                      'sudo://',
                                      [gres3['group_id']], 
                                      'test2_secret',
                                      u'More notés')
        self.assertFalse(sres['error'])

        # Delete the service
        dres = self.vault.service_del(sres['service_id'])
        self.assertTrue(dres is not None)

        res = self.vault.search('.')
        self.assertFalse(res['error'])


    def test_customer_del(self):
        """testing delete a new customer from the vault"""
        cres = self.vault.customer_add(u"Testing é les autres")
        dres = self.vault.customer_del(cres['customer_id'])
        self.assertTrue(dres is not None)

    def test_machine_del(self):
        """testing delete a machine from the vault"""
        cres = self.vault.customer_add(u"Add del it's machines")
        mres = self.vault.machine_add(cres['customer_id'],
                                      "Machine name 3", "fqdn", '4.3.2.1',
                                      None, None)
        self.assertFalse(mres['error'])
        m2res = self.vault.machine_del(mres['machine_id'])
        self.assertFalse(m2res['error'])
        
    def test_alias_del(self):
        """testing delete an alias from the vault"""
        cres = self.vault.customer_add(u"Testing é les autres")
        alias = "c#%d" % cres['customer_id']
        ares = self.vault.cfg.alias_add("myalias", alias)
        dres = self.vault.cfg.alias_del(alias)
        self.assertTrue(dres is not None)

    ## def test_user_del(self):
    ##     """testing delete a user from the vault"""
    ##     ures = self.vault.user_del("test_username")
    ##     self.assertTrue("User removed" in ures['message'])
        #ures = self.vault.user_add("test_admin", True)
        #self.assertTrue("Admin user added" in ures['message'])
        
        #self.assertTrue(False)

    ## def _test_goup_del(self):
    ##     """testing delete a group from the vault"""
    ##     gres = self.vault.group_del("test_group")
    ##     print gres
    ##     self.assertTrue(int(gres['group_id']) > 0)
    ##     #self.assertTrue(False)

    def _test_goup_del_user(self):
        """testing delete a user from a group from the vault"""
        self.assertTrue(False)

    def _test_goup_del_service(self):
        """testing delete a service from a group from the vault"""
        self.assertTrue(False)
