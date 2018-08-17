
from sflvault.api.api_connector import APIConnector


class Customer(APIConnector):

    def __init__(self):
        self.base_url = 'vault/customers/'
        super(Customer, self).__init__()

    def get_customer_list(self):
        return self.get_all_instance()

    def get_single_customer(self, customer_id):
        return self.get_single_instance(customer_id)

    def update_customer(self, customer_id, data):
        return self.update_single_instance(customer_id, data)

    def delete_customer(self, customer_id):
        return self.delete_single_instance(customer_id)

    def new_customer(self, data):
        return self.new_single_instance(data)
