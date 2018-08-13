import os
# Python3
try:
    from urllib.parse import urljoin
# Python2
except ImportError:
    from urlparse import urljoin


from sflvault.services.service_group import ServiceGroup

test_server_url = os.getenv("VAULT_SERVER")
json_data = '{"id":1,"name":"django","created":"2018-08-13","fqdn":"vault.server/","ip":"192.168.0.1","location":"test","notes":"Test note","customer":2}'
service_group = ServiceGroup()
service_group_id = 1


def test_get_service_group_list(requests_mock):

    requests_mock.get(urljoin(test_server_url, service_group.base_url), json=json_data)

    response_get_service_group_list = service_group.get_service_group_list()

    assert(response_get_service_group_list.json() == json_data)
    assert(response_get_service_group_list.status_code == 200)


def test_get_single_service_group(requests_mock):
    requests_mock.get(urljoin(test_server_url, "{}{}/".format(service_group.base_url, service_group_id)), json=json_data)
    response_get_single_service_group = service_group.get_single_service_group(1)

    assert(response_get_single_service_group.json() == json_data)
    assert(response_get_single_service_group.status_code == 200)


def test_delete_service_group(requests_mock):
    requests_mock.delete(urljoin(test_server_url, "{}{}/".format(service_group.base_url, service_group_id)), status_code=204)
    response_delete_service_group = service_group.delete_service_group(1)

    assert(response_delete_service_group.status_code == 204)


def test_update_service_group(requests_mock):
    requests_mock.put(urljoin(test_server_url, "{}{}/".format(service_group.base_url, service_group_id)), json=json_data)
    response_update_service_group = service_group.update_service_group(1, json_data)

    assert(response_update_service_group.json() == json_data)
    assert(response_update_service_group.status_code == 200)


def test_new_service_group(requests_mock):
    requests_mock.post(urljoin(test_server_url, service_group.base_url), json=json_data, status_code=201)
    response_new_service_group = service_group.new_service_group(json_data)

    assert(response_new_service_group.json() == json_data)
    assert(response_new_service_group.status_code == 201)
