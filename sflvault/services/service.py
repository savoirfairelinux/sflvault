
from sflvault.api.api_connector import APIConnector


class Service(APIConnector):

    def __init__(self):
        self.base_url = 'vault/services/'
        super(Service, self).__init__()

    def get_service_list(self):
        return self.get_all_instance()

    def get_single_service(self, service_id):
        return self.get_single_instance(service_id)

    def update_service(self, service_id, data):
        return self.update_single_instance(service_id, data)

    def delete_service(self, service_id):
        return self.delete_single_instance(service_id)

    def new_service(self, data):
        return self.new_single_instance(data)
