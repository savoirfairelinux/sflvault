from sflvault.tests import *

class TestXmlrpcController(TestController):

    def test_index(self):
        response = self.app.get(url_for(controller='xmlrpc'))
        # Test response...
