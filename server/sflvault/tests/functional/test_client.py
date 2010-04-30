# -=- encoding: utf-8 -=-
from sflvault.tests import TestController
from sflvault.common.crypto import *
from sflvault.client.client import authenticate

import logging

log = logging.getLogger('tester')

class TestVaultController(TestController):
    
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
        res = self.vault.service_add(cres['customer_id'], 
                                     mres['machine_id'],
                                     0, 
                                     'ssh://marrakis@localhost',
                                     [], 
                                     'test',
                                     '')
        self.assertFalse("Error adding service" in res['message'])

    def test_alias_add(self):
        """testing add a new alias to the vault"""
        cres = self.vault.customer_add(u"Testing é les autres")
        ares = self.vault.alias_add("#%s"%cres['customer_id'], 'c#1')
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
        """testing add a user to a group to the vault"""
        gres1 = self.vault.group_add("test_group1_user")
        gres2 = self.vault.group_add("test_group2_user")

        gares1 = self.vault.group_add_user(gres1['group_id'], 1)
        gares2 = self.vault.group_add_user(gres2['group_id'], 1, True)

        self.assertFalse("Error adding user to group" in gares1)
        self.assertFalse("Error adding user to group" in gares2)

    def test_group_add_service(self):
        """testing add a service to a group to the vault"""
        gres3 = self.vault.group_add("test_group3_user")
        cres = self.vault.customer_add(u"Testing é les autres")
        gares1 = self.vault.group_add_user(gres3['group_id'], 1)
        mres = self.vault.machine_add(str(cres['customer_id']), 
                                      "Machine name 3",
                                      "domain1.example2.com", 
                                      '4.3.2.1',
                                      None, 
                                      None)
        res = self.vault.service_add(cres['customer_id'], 
                                     mres['machine_id'],
                                     0, 
                                     'ssh://marrakis@localhost',
                                     [], 
                                     'test',
                                     '')
        gares3 = self.vault.group_add_service(gres3['group_id'], res['service_id'])

        self.assertFalse("Error adding service to group" in gares3)

    def test_customer_del(self):
        """testing delete a new customer from the vault"""
        cres = self.vault.customer_add(u"Testing é les autres")
        dres = self.vault.customer_del(cres['customer_id'])
        self.assertTrue(dres is not None)

    def test_machine_del(self):
        """testing delete a machine from the vault"""
        cres = self.vault.customer_add(u"Testing é les autres")
        mres = self.vault.machine_add(str(cres['customer_id']), "Machine name 3",
                                      "domain1.example2.com", '4.3.2.1',
                                      None, None)
        self.assertTrue(mres is not None)

    def test_service_del(self):
        """testing delete a service from the vault"""
        cres = self.vault.customer_add(u"Testing é les autres")
        mres = self.vault.machine_add(str(cres['customer_id']), 
                                      "Machine name 3",
                                      "domain1.example2.com", 
                                      '4.3.2.1',
                                      None, 
                                      None)
        sres = self.vault.service_add(cres['customer_id'], 
                                      mres['machine_id'],
                                      0, 
                                      'ssh://marrakis@localhost',
                                      [], 
                                      'test',
                                      '')
        sres = self.vault.service_del(sres['service_id'])
        self.assertTrue(sres is not None)

        
    def test_alias_del(self):
        """testing delete an alias from the vault"""
        cres = self.vault.customer_add(u"Testing é les autres")
        ares = self.vault.alias_add("#%s"%cres['customer_id'], 'c#23')
        dres = self.vault.alias_del('c#23')
        self.assertTrue(dres is not None)

    def test_user_del(self):
        """testing delete a user from the vault"""
        self.assertTrue(False)

    def test_goup_del(self):
        """testing delete a group from the vault"""
        self.assertTrue(False)

    def test_goup_del_user(self):
        """testing delete a user from a group from the vault"""
        self.assertTrue(False)

    def test_goup_del_service(self):
        """testing delete a service from a group from the vault"""
        self.assertTrue(False)
