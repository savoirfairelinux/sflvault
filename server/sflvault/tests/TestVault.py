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
from sflvault.common import VaultError

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
        ures = self.vault.user_add("test_username", False)
        self.assertTrue("User added" in ures['message'])
        ures = self.vault.user_add("test_admin", True)
        self.assertTrue("Admin user added" in ures['message'])

    def test_user_add_extend_expired_setup(self):
        """ If a user is added, and setup_timeout expires, 
        adding it again should extend the setup period"""

        ures = self.vault.user_add("test_username", False)
        self.assertTrue("User added" in ures['message'])
        
        # timeout
        import time; time.sleep(2)

        ures = self.vault.user_add("test_username", False)
        self.assertTrue("had setup timeout expired" in ures['message'])

        
    def test_cannot_readd_user_before_expire(self):
        """ If a user is added, user_add cannot be called agin
        before the setup time expires """

        ures = self.vault.user_add("test_username", False)
        self.assertTrue("User added" in ures['message'])

        self.assertRaises(VaultError,
                          self.vault.user_add,
                          "test_username",
                          False)


    def test_group_add(self):
        """testing add a new group to the vault"""
        gres = self.vault.group_add("test_group")
        self.assertTrue(int(gres['group_id']) > 0)

    def test_group_put_invalid(self):
        self.assertRaises(VaultError,
                          self.vault.group_put,
                          "invalid id",
                          {'name': 'invalid param' })


    def test_group_put_name(self):
        response = self.vault.group_add("other_test_group")
        group_id = response['group_id']
        response2 = self.vault.group_put(group_id, {'name': 'other_test_group_changed'})
        self.assertFalse(response2['error'])

        response3 = self.vault.group_get(group_id)
        self.assertEquals(response3['name'], 'other_test_group_changed')

    def test_group_put_hidden(self):
        response = self.vault.group_add("other_test_group")
        group_id = response['group_id']
        response2 = self.vault.group_put(group_id, {'hidden': True})
        self.assertFalse(response2['error'])

    def test_add_user_and_user_setup(self):
        """testing add a user to the vault and setup passphrase"""
        def givepass():
                return 'passphrase'
        ures1 = self.vault.user_add('testuser', False)
        self.assertTrue(ures1 is not None)
        tmp_vault = SFLvaultClient(self.getConfFileUser(), shell=True)
        ures2 = tmp_vault.user_setup('testuser',
                                     'http://localhost:6555/vault/rpc',
                                     'passphrase')

        self.assertTrue(ures2 is not None)
        

    def test_user_setup_no_user(self):
        tmp_vault = SFLvaultClient(self.getConfFileUser(), shell=True)

        self.assertRaises(VaultError,
                          tmp_vault.user_setup,
                          'invalid user',
                          'http://localhost:6555/vault/rpc',
                          'passphrase')

    def test_user_setup_already_has_public_key(self):
        """ A user cannot do his setup twice """
        ures1 = self.vault.user_add('testuser', False)
        self.assertTrue(ures1 is not None)
        tmp_vault = SFLvaultClient(self.getConfFileUser(), shell=True)
        ures2 = tmp_vault.user_setup('testuser',
                                     'http://localhost:6555/vault/rpc',
                                     'passphrase')

        self.assertTrue(ures2 is not None)

        tmp_vault = SFLvaultClient(self.getConfFileUser(), shell=True)
        self.assertRaises(VaultError,
                          tmp_vault.user_setup,
                          'testuser',
                          'http://localhost:6555/vault/rpc',
                          'passphrase')
   
    def test_user_setup_expired(self):
        import time

        tmp_vault = SFLvaultClient(self.getConfFileUser(), shell=True)

        self.vault.user_add('testuser', False)
        time.sleep(5)

        self.assertRaises(VaultError,
                          tmp_vault.user_setup,
                          'testuser',
                          'http://localhost:6555/vault/rpc',
                          'passphrase')
                                 

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
    
    def test_group_list(self):
        response = self.vault.group_list()
        self.assertTrue(len(response['list']) == 0)
        self.vault.group_add('test')
        response2 = self.vault.group_list()
        group_list = response2['list']
        self.assertTrue(len(group_list) == 1)
        self.assertTrue(group_list[0]['id'] == 1)
        self.assertTrue(group_list[0]['name'] == 'test')

        self.assertFalse(response['error'])

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

    def test_search_invalid_filter_type(self):
        """ A search that uses an invalid filter format should fail
        with a vaultError. However, there is no way to test this 
        behaviour using the client, as it will try to turn any query
        in a dictionary and fail premptively """
        #self.assertRaises(VaultError, 
        #                  self.vault.search,
        #                  'service_del',
        #                  filters=['invalid',])
        pass 

    def test_search_skip_unspecified_and_none_filters(self):
        """ Unspecified filters should be skipped, and they
        should not affect the search"""
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
        ## Search for service afterwards
        search = self.vault.search('service_del')
        self.assertTrue(len(search['results'].items()) ==1)

        # Adds all sort of crazy filters!
        search2 = self.vault.search('service_del',
                          filters={
                              # Unspecified filters
                              'color': 'red',
                              'height': '2 meters',
                              'bogomips': 5.5,
                              'anxiety': None,
                              # None values for specified filters
                              'groups': None,
                              'machines': None,
                              'customers': None
                          })

        self.assertTrue(len(search2['results'].items()) ==1)        
                              
    def test_search_fail_on_invalid_filters(self):
        """ When an invalid filter value is specified, it should fail """
        self.assertRaises(VaultError,
                          self.vault.search,
                          'service_del',
                          filters={'machines': ['invalid', 'filter', 'value'] })

    def test_search_filters_narrow_results(self):
        """ Search can be filtered by machine, groups and customers """
        # Adds three services. Each one has a different customer
        # a different machine and a different group.

        service1 = self._add_new_service()
        service2 = self._add_new_service()
        service3 = self._add_new_service()

        self.assertFalse(service1['error'] or
                         service2['error'] or
                         service3['error'])

        # however, they're all for sflvault.org so searching for that
        # should return all three.
        
        search = self.vault.search('sflvault.org')
        self.assertEquals(len(search['results']), 3)

        # Now let's tailor the search to match one of the services
        response = self.vault.service_get(service1['service_id'])
        response2 = self.vault.machine_get(response['machine_id'])

        response3 = self.vault.service_get(service2['service_id'])
        response4 = self.vault.machine_get(response3['machine_id'])

        search2 = self.vault.search('sflvault.org',
                                    filters={
                                        'machines': [response['machine_id']],
                                        'groups': [response['group_id']],
                                        'customers': [response2['customer_id']],
                                    })

        self.assertEquals(len(search2['results']), 1)


        # Multiple search criteria creates the union of the results

        machines = [response['machine_id'], response3['machine_id']]
        groups = [response['group_id'], response3['group_id']]
        customers = [response2['customer_id'], response4['customer_id']]

        search2 = self.vault.search('sflvault.org',
                                    filters={
                                        'machines': machines,
                                        'groups': groups,
                                        'customers': customers
                                    })

        self.assertEquals(len(search2['results']), 2)


    def test_user_del(self):
        """testing delete a user from the vault"""
        cres = self.vault.user_add(u"Utilisateur de test")
        self.assertTrue(cres is not None)
        dres = self.vault.user_del(u"Utilisateur de test")
        self.assertTrue(dres is not None)

    def test_cannot_user_del_twice(self):
        """ Cannot delete a user twice from the vault """
        cres = self.vault.user_add(u"Utilisateur de test")
        self.assertTrue(cres is not None)
        dres = self.vault.user_del(u"Utilisateur de test")
        self.assertRaises(VaultError,
                          self.vault.user_del,
                          u"Utilisateur de test")

    def test_group_del(self):
        """testing delete a group from the vault"""
        cres = self.vault.group_add('test group')
        self.assertTrue(cres is not None)
        dres = self.vault.group_del(cres['group_id'])
        self.assertTrue(dres is not None)

    def test_group_del_cascade(self):
        """ Tests deleting a group and all it's services """

        machine = self._add_new_machine()
        response = self.vault.group_add('test group')
        self.assertFalse(response['error'])

        response2 = self.vault.service_add(machine['machine_id'],
                                          0,
                                          'ssh://sflvault.org',
                                          [response['group_id']],
                                          'secret') 
                                           
        self.assertFalse(response2['error'])

        response4 = self.vault.group_del(response['group_id'],
                                         delete_cascade=True)
        self.assertFalse(response4['error'])

        self.assertRaises(VaultError,
                          self.vault.service_get,
                          response2['service_id'])

    def test_group_del_cascade_error(self):
        response = self.vault.group_add('test group')
        response2 = self._add_new_service()
        self.assertFalse(response['error'] or response2['error'])
        response3 = self.vault.group_add_service(response['group_id'],
                                                 response2['service_id'])

        self.assertRaises(VaultError,
                          self.vault.group_del,
                          response['group_id'])

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

    def test_user_list(self):
        response = self.vault.user_list()
        self.assertFalse(response['error'])
        self.assertTrue(len(response['list']) == 1)
        
        admin = response['list'][0]
        self.assertEquals(admin['username'], 'admin')
        self.assertFalse(admin['setup_expired'])
        self.assertFalse(admin['waiting_setup'])
        self.assertTrue('created_stamp' in admin)
        self.assertTrue(admin['is_admin'])
        self.assertEquals(admin['id'], 1)

        # there is initially only one user
        response = self.vault.user_list()
        self.assertFalse(response['error'])
        self.assertEquals(len(response['list']), 1)

        response2 = self.vault.user_add('dcormier')
        self.assertFalse(response2['error'])

        # there should now be two users        
        response3 = self.vault.user_list()
        self.assertFalse(response3['error'])
        self.assertEquals(len(response3['list']), 2)


    def test_service_get_invalid_service(self):
        # Try to get a service that we are sure doesn't
        # exist
        from sflvault.common import VaultError

        self.assertRaises(VaultError,
                          self.vault.service_get,
                          100)

        # Adds a service and retrieves it
        response2 = self._add_new_service()
        response3 = self.vault.service_get(response2['service_id'])
        self.assertEquals(response3['id'], response2['service_id'])
        
        # We shouldn't be able to retrieve this service
        # for a group it is not tied to.

        # FIXME: there is no way to pass group_id in vault.py

        #self.assertRaises(VaultError, self.vault.service_get(response2['service_id'],
        #                                                     group_id='invalid'))

    def test_customer_put_and_get(self):
        response = self._add_new_customer()
        response2 = self.vault.customer_put(response['customer_id'],
                                      {'name': 'dcormier' })
        response3 = self.vault.customer_get(response['customer_id'])

        self.assertEquals(response3['id'],
                          response['customer_id'])

        self.assertEquals(response3['name'],
                          'dcormier')


    def test_machine_put_and_get(self):
        response = self._add_new_machine()
        self.assertFalse(response['error'])
        
        machine_data = { 'ip': '127.0.0.1',
                         'name': 'sflvault',
                         'fqdn': 'sflvault',
                         'location': 'sfl',
                         'notes': 'super machine' }

        response2 = self.vault.machine_put(response['machine_id'],
                                           machine_data)

        machine = self.vault.machine_get(response['machine_id'])
        self.assertEquals(machine['ip'], '127.0.0.1')
        self.assertEquals(machine['name'], 'sflvault')
        self.assertEquals(machine['fqdn'], 'sflvault')
        self.assertEquals(machine['location'], 'sfl')
        self.assertEquals(machine['notes'], 'super machine')
    
    def test_service_put(self):
        response = self._add_new_service()
        my_note = 'new notes'
        my_url = 'http://sflphone.org'
        service_data = {'notes': my_note,
                        'url': my_url }

        response2 = self.vault.service_put(response['service_id'],
                                           service_data)
        self.assertFalse(response2['error'])

        response3 = self.vault.service_get(response['service_id'])

        self.assertEquals(response3['notes'], my_note)
        self.assertEquals(response3['url'], my_url)
        self.assertEquals(response3['id'], response['service_id'])
        
    def test_cannot_put_on_nonexistent_service(self):
        """ Asserts that we cannot call service_put on 
        a nonexistent service """
        self.assertRaises(VaultError,
                          self.vault.service_put,
                          1,
                          {'notes': 'my notes'})
                          

    def test_group_del_service(self):
        group = self._add_new_group()
        service = self._add_new_service()
        
        # there should not be any association between the group and the
        # service
        service_get = self.vault.service_get(service['service_id'],
                                             group_id=group['group_id'])


        self.assertTrue(service_get['group_id'] == '')


        # We add the service to the new group
        group_add_service = self.vault.group_add_service(group['group_id'],
                                                         service['service_id'])
        self.assertFalse(group_add_service['error'])

        # The service should now be part of the group
        service_get2 = self.vault.service_get(service['service_id'])

        

        self.assertTrue(group['group_id'] == service_get2['group_id'])

        # And then we remove it
        service_del = self.vault.group_del_service(group['group_id'],
                                                   service['service_id'])

        # It should not be there anymore
        service_get3 = self.vault.service_get(service['service_id'])
        self.assertTrue(service_get['group_id'] == '')


    def test_group_del_service_from_original_group(self):
        machine = self._add_new_machine()
        original_group = self._add_new_group()

        # if we create a service and add it to an original group
        service = self.vault.service_add(machine['machine_id'],
                                      0,
                                      'ssh://sflvault.org',
                                      [original_group['group_id']],
                                      'secret') 

        # if we try to remove it from this group, there should be an error
        self.assertRaises(VaultError,
                          self.vault.group_del_service,
                          original_group['group_id'],
                          service['service_id'])

        # however, if we add it to another group...
        new_group = self._add_new_group()
        group_add_service = self.vault.group_add_service(new_group['group_id'],
                                                         service['service_id'])
        self.assertFalse(group_add_service['error'])

        # we should be able to remove it from the original group!
        response = self.vault.group_del_service(original_group['group_id'],
                                                service['service_id'])
        self.assertFalse(response['error'])
        

    def test_service_get_tree(self):
        """ tests that we can get a service and it's tree of parent / sub services"""
        response = self._add_new_service()
        response2 = self.vault.service_get_tree(response['service_id'])
        self.assertEquals(len(response2), 1)


    def test_service_get_tree_circular_reference_fail(self):
        """ If there are circular references in service definitions,
        service_get_tree should fail """
        response = self._add_new_service()
        response2 = self._add_new_service()

        service_data = { 'parent_service_id': response2['service_id'] }
        service2_data = { 'parent_service_id': response['service_id'] }

        sput = self.vault.service_put(response['service_id'],
                                      service_data)

        sput2 = self.vault.service_put(response2['service_id'],
                                      service2_data)

        self.assertFalse(sput['error'] or sput2['error'])

        # Now both services should get an error when we try to get them
        self.assertRaises(VaultError,
                          self.vault.service_get_tree,
                          response['service_id'])

        self.assertRaises(VaultError,
                          self.vault.service_get_tree,
                          response2['service_id'])
                          


    def test_customer_list(self):
        # FIXME: remove customer_id from client.py

        customer_add = self.vault.customer_add('dcormier')
        customer_add2 = self.vault.customer_add('dcormier2')
        self.assertFalse(customer_add['error'] or customer_add2['error'])

        customer_list = self.vault.customer_list()['list']
        self.assertEquals(len(customer_list), 2)
        self.assertEquals(customer_list[0]['name'], 'dcormier')
        self.assertEquals(customer_list[1]['name'], 'dcormier2')
    def test_machine_list(self):
        machine1 = self._add_new_machine()
        machine2 = self._add_new_machine()
        
        machine_list_response = self.vault.machine_list()
        self.assertFalse(machine_list_response['error'])
        
        machine_list = machine_list_response['list']
        self.assertEquals(len(machine_list), 2)


    def test_machine_list_of_customer(self):

        # adds a customer and a machine
        customer = self.vault.customer_add('dcormier')
        machine1 = self._add_new_machine()

        # customer should not have any machine
        machine_list_response = self.vault.machine_list(customer_id=customer['customer_id'])
        machine_list = machine_list_response['list']
        self.assertEquals(len(machine_list), 0)

        # changes the owner of the machine to the previously added customer
        machine_put = self.vault.machine_put(machine1['machine_id'],
                                             {'customer_id': customer['customer_id']})

        self.assertFalse(machine_put['error'])
        
        # customer should now have one machine
        machine_list_response2 = self.vault.machine_list(customer_id=customer['customer_id'])
        machine_list2 = machine_list_response2['list']
        self.assertEquals(len(machine_list2), 1)
        self.assertEquals(machine_list2[0]['customer_id'],
                          customer['customer_id'])

        # let's change the owner again to an invalid customer
        machine_put2 = self.vault.machine_put(machine1['machine_id'],
                                              {'customer_id': 37})

        self.assertFalse(machine_put2['error'])

        # our previous customer should not have any machine
        machine_list_response3 = self.vault.machine_list(
            customer_id=customer['customer_id'])

        machine_list3 = machine_list_response3['list']
        self.assertEquals(len(machine_list3), 0)

