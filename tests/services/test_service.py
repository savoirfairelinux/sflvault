import os
# Python3
try:
    from urllib.parse import urljoin
# Python2
except ImportError:
    from urlparse import urljoin

from sflvault.services.service import Service

test_server_url = os.getenv("VAULT_SERVER")
json_data = '{"id":1,"created":"2018-08-13","updated":"2018-08-13","url":"https://vault.server/","metadata":{},"notes":"Test","secret":"Test","service_group":1,"parent":2}'
service = Service()
service_id = 1


def test_get_service_list(requests_mock):
    requests_mock.get(urljoin(test_server_url, service.base_url), json=json_data)

    response_get_service_list = service.get_service_list()

    assert(response_get_service_list.json() == json_data)
    assert(response_get_service_list.status_code == 200)


def test_get_single_service(requests_mock):
    requests_mock.get(urljoin(test_server_url, "{}{}/".format(service.base_url, service_id)),json=json_data)

    response_get_single_service = service.get_single_service(service_id)

    assert(response_get_single_service.json() == json_data)
    assert(response_get_single_service.status_code == 200)


def test_update_service(requests_mock):
    requests_mock.put(urljoin(test_server_url, "{}{}/".format(service.base_url, service_id)), json=json_data)

    response_update_service = service.update_service(service_id, json_data)

    assert(response_update_service.json() == json_data)
    assert(response_update_service.status_code == 200)


def test_delete_service(requests_mock):
    requests_mock.delete(urljoin(test_server_url, "{}{}/".format(service.base_url, service_id)) ,status_code=204)

    response_delete_service = service.delete_service(service_id)

    assert(response_delete_service.status_code == 204)


def test_new_service(requests_mock):
    requests_mock.post(urljoin(test_server_url, service.base_url), json=json_data, status_code=201)

    response_new_service = service.new_service(json_data)

    assert(response_new_service.json() == json_data)
    assert(response_new_service.status_code == 201)
