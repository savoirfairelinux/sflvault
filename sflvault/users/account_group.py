
from sflvault.api.api_connector import APIConnector


class AccountGroup(APIConnector):

    def __init__(self):
        self.base_url = 'vault/account_groups/'
        super(AccountGroup, self).__init__()

    def get_account_group_list(self):
        return self.get_all_instance()

    def get_single_account_group(self, account_group_id):
        return self.get_single_instance(account_group_id)

    def update_account_group(self, account_group_id, data):
        return self.update_single_instance(account_group_id, data)

    def delete_account_group(self, account_group_id):
        return self.delete_single_instance(account_group_id)

    def new_account_group(self, data):
        return self.new_single_instance(data)
