
from sflvault.api.api_connector import APIConnector


class ServiceGroup(APIConnector):

    def __init__(self):
        self.base_url = 'vault/service_groups/'
        super(ServiceGroup, self).__init__()

    def get_service_group_list(self):
        return self.get_all_instance()

    def get_single_service_group(self, service_group_id):
        return self.get_single_instance(service_group_id)

    def update_service_group(self, service_group_id, data):
        return self.update_single_instance(service_group_id, data)

    def delete_service_group(self, service_group_id):
        return self.delete_single_instance(service_group_id)

    def new_service_group(self, data):
        return self.new_single_instance(data)
