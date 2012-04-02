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

from sflvault.tests import TestController
from sflvault.common.crypto import *
from sflvault.client.client import authenticate
from sflvault.client.client import SFLvaultConfig, SFLvaultClient
import logging
import random

log = logging.getLogger('tester')

class TestVaultController(TestController):
    

    def _rand_name(self):
        return '%s' % str(random.randint(0,1000))

    def _add_new_group(self):
        """Adds a new group with a random name"""
        return self.vault.group_add(self._rand_name())

    def _add_new_customer(self):
        """Adds a new customer with a random name"""
        return self.vault.customer_add(self._rand_name())

    def _add_new_machine(self):
        """Adds a new machine with a random name, linked to a new customer that also have a random name"""
        cid = self._add_new_customer()
        mid = self.vault.machine_add(cid['customer_id'], self._rand_name())
        return mid
    def _add_new_service(self):
        mid = self._add_new_machine()
        gid = self._add_new_group()
        return self.vault.service_add(mid['machine_id'],
                               0,
                               'ssh://sflvault.org',
                               [gid['group_id']],
                               'secret') 
        

    def setUp(self):
        self.vault = self.getVault()

    def test_customer_add(self):
        """testing add a new customer to the vault"""
        res = self.vault.customer_add('testing customer 1 2 3')
        cid1 = res['customer_id']
        self.assertTrue(cid1, 1)
        self.assertEqual(res['message'], 'Customer added')

    def test_machine_add(self):
        """testing add a new machine to the vault"""
        res = self.vault.customer_add(u"Testing é les autres")
        cid2 = res['customer_id']
        self.assertEqual(res['message'], 'Customer added')    
        res = self.vault.machine_add(str(cid2), 
                                     "Machine name 2",
                                     "domain1.example2.com", 
                                     '4.3.2.1',
                                     None, 
                                     None)
        self.assertFalse("Error adding machine" in res['message'])

    def test_service_add(self):
        """testing add a new service to the vault"""
        cres = self.vault.customer_add(u"Testing é les autres")
        mres = self.vault.machine_add(str(cres['customer_id']), 
                                      "Machine name 3",
                                      "domain1.example2.com", 
                                      '4.3.2.1',
                                      None, 
                                      None)
        res = self.vault.service_add(mres['machine_id'],
                                     0, 
                                     'ssh://marrakis@localhost',
                                     [], 
                                     'test',
                                     '')
        self.assertFalse("Error adding service" in res['message'])

    def test_alias_add(self):
        """testing add a new alias to the vault"""
        cres = self.vault.customer_add(u"Testing é les autres")
        ares = self.vault.cfg.alias_add("customer#%s"%cres['customer_id'], "c#%s" % cres['customer_id'])
        self.assertTrue(ares)

    def test_alias_del(self):
        cres = self.vault.cfg.alias_add('customer 1', 'u#1')
        self.assertTrue(cres)
        dres = self.vault.cfg.alias_del('customer 1')
        self.assertTrue(dres)

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

    def test_add_user_and_user_setup(self):
        """testing add a user to the vault and setup passphrase"""
        def givepass():
                return 'passphrase'
        ures1 = self.vault.user_add('testuser')
        self.assertTrue(ures1 is not None)
        tmp_vault = SFLvaultClient(self.getConfFileUser(), shell=True)
        ures2 = tmp_vault.user_setup('testuser',
                                     'http://localhost:6555/vault/rpc',
                                     'passphrase')

        self.assertTrue(ures2 is not None)
        
    def test_group_add_user(self):
        """testing add a user to a group to the vault"""
        ures1 = self.vault.user_add('test_add_user_group_vault')
        self.assertTrue(ures1 is not None)
        tmp_vault = SFLvaultClient(self.getConfFileUser())
        ures2 = tmp_vault.user_setup('test_add_user_group_vault',
                                     'http://localhost:6555/vault/rpc',
                                     'passphrase')
        self.assertTrue(ures2 is not None)
        
        log.warn(ures1)
        log.warn(ures2)
    
        gres1 = self.vault.group_add("test_group1_user")
        gres2 = self.vault.group_add("test_group2_user")

        gares1 = self.vault.group_add_user(gres1['group_id'], ures1['user_id'])
        gares2 = self.vault.group_add_user(gres2['group_id'], ures1['user_id'], True)

        self.assertTrue("Added user to group successfully" in gares1['message'])
        self.assertFalse("Error adding user to group" in gares2['message'])

    def test_group_add_service(self):
        """testing add a service to a group to the vault"""
        gres3 = self.vault.group_add("test_group3_user")
        cres = self.vault.customer_add(u"Testing é les autres")
        mres = self.vault.machine_add(str(cres['customer_id']), 
                                      "Machine name 3",
                                      "domain1.example2.com", 
                                      '4.3.2.1',
                                      None, 
                                      None)
        res = self.vault.service_add(mres['machine_id'],
                                     None, 
                                     'ssh://marrakis@localhost',
                                     [gres3['group_id']], 
                                     'test',
                                     '')
       # gares3 = self.vault.group_add_service(gres3['group_id'], res['service_id'])

        self.assertTrue(res is not None)

    def test_customer_del(self):
        """testing delete a new customer from the vault"""
        cres = self.vault.customer_add(u"Testing é les autres")
        dres = self.vault.customer_del(cres['customer_id'])
        self.assertTrue("Deleted customer c#%s successfully" % cres['customer_id'] in dres['message'])

    def test_service_passwd(self):
        sres = self._add_new_service()
        pres = self.vault.service_passwd(sres['service_id'], 'new_secret')
        self.assertEqual("Password updated for service.", pres['message'])
        self.assertEqual(sres['service_id'], pres['service_id'])

    def test_machine_del(self):
        """testing delete a machine from the vault"""
        cres = self.vault.customer_add(u"Testing é les autres")
        mres = self.vault.machine_add(str(cres['customer_id']), "Machine name 3",
                                      "domain1.example2.com", '4.3.2.1',
                                      None, None)
        dres = self.vault.machine_del(mres['machine_id'])
        self.assertTrue('Deleted machine m#%s successfully' % mres['machine_id'] in dres['message'])

    def test_service_del(self):
        """testing delete a service from the vault"""
        cres = self.vault.customer_add(u"Testing é les autres")
        mres = self.vault.machine_add(str(cres['customer_id']), 
                                      "Machine name 3",
                                      "domain1.example2.com", 
                                      '4.3.2.1',
                                      None, 
                                      None)
        sres = self.vault.service_add(mres['machine_id'],
                                      0, 
                                      u'ssh://service_del',
                                      [], 
                                      'test',
                                      '')
        sres = self.vault.service_del(sres['service_id'])
        self.assertTrue(sres is not None)

        ## Search for service afterwards
        search = self.vault.search('service_del')
        self.assertTrue(len(search['results'].items()) == 0)

    def test_user_del(self):
        """testing delete a user from the vault"""
        cres = self.vault.user_add(u"Utilisateur de test")
        self.assertTrue(cres is not None)
        dres = self.vault.user_del(u"Utilisateur de test")
        self.assertTrue(dres is not None)

    def test_group_del(self):
        """testing delete a group from the vault"""
        cres = self.vault.group_add('test group')
        self.assertTrue(cres is not None)
        dres = self.vault.group_del(cres['group_id'])
        self.assertTrue(dres is not None)

    def test_group_del_user(self):
        """testing delete a user from a group from the vault"""
        #Add test user
        ures1 = self.vault.user_add('testuser2')
        self.assertTrue(ures1 is not None)
        tmp_vault = SFLvaultClient(self.getConfFileUser(), shell=True)
        ures2 = tmp_vault.user_setup('testuser2',
                                     'http://localhost:6555/vault/rpc',
                                     'passphrase')
        self.assertTrue(ures2 is not None)
        gcres = self.vault.group_add(u'Test group del user')
        uares = self.vault.group_add_user(gcres['group_id'], 'testuser2')
        udres = self.vault.group_del_user(gcres['group_id'], 'testuser2')
        self.assertTrue("Removed user from group successfully" in udres['message'])

#    def test_group_del_service(self):
#        """testing delete a service from a group from the vault"""
#        self.assertTrue(False)
