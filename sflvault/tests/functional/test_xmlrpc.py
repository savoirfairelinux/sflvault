from sflvault.tests import *
from sflvault.lib.common.crypto import *




class TestXmlrpcController(TestController):

    def test_1_user_setup(self):
        """Test the user-setup command"""
        def givepass():
            return self.passphrase
        
        self.vault.user_setup(self.username, None, self.passphrase)
        self.vault.set_getpassfunc(givepass)

    def test_2_pouet(self):
        pass
