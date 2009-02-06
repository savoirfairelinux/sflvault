# -=- encoding: utf-8 -=-

from sflvault.tests import *
from sflvault.lib.common.crypto import *




class TestVaultController(TestController):

    def test_1_user_setup(self):
        """Test the user-setup command"""
        def givepass():
            return self.passphrase
        
        self.vault.set_getpassfunc(givepass)
        self.vault.user_setup(self.username, 'http://localhost:5551/vault/rpc',
                              self.passphrase)


        res = self.vault.customer_add('testing customer 1 2 3')
        self.cid1 = 1


        res = self.vault.customer_add(u"Testing é les autres")
        self.cid2 = 2


        res = self.vault.machine_add(int(self.cid1), "Machine name 1",
                                     "domain1.example.com", '1.2.3.4',
                                     'California', None)
        self.mid1 = 1

        
        res = self.vault.machine_add(str(self.cid2), "Machine name 2",
                                     "domain1.example2.com", '4.3.2.1',
                                     None, None)
        self.mid2 = 2
