import os

# Python3
try:
    from urllib.parse import urljoin
# Python2
except ImportError:
    from urlparse import urljoin
from sflvault.api.api import APIHandler


# Always add a forward slash at the end of each url
class APIConnector(object):

    def __init__(self):

        self.api = APIHandler(os.getenv("VAULT_SERVER"))

    def get_all_instance(self):
        return self.api.get(self.base_url)

    def get_single_instance(self, id):
        return self.api.get(urljoin(self.base_url, "{}{}".format(id, '/')))

    def update_single_instance(self, id, data):
        return self.api.put(urljoin(self.base_url, "{}{}".format(id, '/')), data)

    def delete_single_instance(self, id):
        return self.api.delete(urljoin(self.base_url, "{}{}".format(id, '/')))

    def new_single_instance(self, data):
        return self.api.post(self.base_url, data)
