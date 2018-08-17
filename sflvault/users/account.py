
from sflvault.api.api_connector import APIConnector


class Account(APIConnector):

    def __init__(self):
        self.base_url = 'vault/accounts/'
        super(Account, self).__init__()

    def get_account_list(self):
        return self.get_all_instance()

    def get_single_account(self, account_id):
        return self.get_single_instance(account_id)

    def update_account(self, account_id, data):
        return self.update_single_instance(account_id, data)

    def delete_account(self, account_id):
        return self.delete_single_instance(account_id)

    def new_account(self, data):
        return self.new_single_instance(data)
