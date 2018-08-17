import os
# Python3
try:
    from urllib.parse import urljoin
# Python2
except ImportError:
    from urlparse import urljoin

from sflvault.services.customer import Customer

test_server_url = os.getenv("VAULT_SERVER")
json_data = '[{"id": 1, "name": "client", "created": "2018-08-13", "created_by": null}]'
customer = Customer()
customer_id = 1


def test_get_customer_list(requests_mock):

    requests_mock.get(urljoin(test_server_url, customer.base_url), json=json_data)

    response_get_customer_list = customer.get_customer_list()

    assert(response_get_customer_list.json() == json_data)
    assert(response_get_customer_list.status_code == 200)


def test_get_single_customer(requests_mock):

    requests_mock.get(urljoin(test_server_url, "{}{}/".format(customer.base_url, customer_id)), json=json_data)

    response_get_single_customer = customer.get_single_customer(1)

    assert(response_get_single_customer.json() == json_data)
    assert(response_get_single_customer.status_code == 200)


def test_delete_single_customer(requests_mock):

    requests_mock.delete(urljoin(test_server_url, "{}{}/".format(customer.base_url, customer_id)), status_code=204)

    response_delete_customer = customer.delete_customer(1)

    assert(response_delete_customer.status_code == 204)


def test_new_customer(requests_mock):

    requests_mock.post(urljoin(test_server_url, customer.base_url), status_code=201, json=json_data)

    response_new_customer = customer.new_customer(json_data)

    assert(response_new_customer.json() == json_data)
    assert(response_new_customer.status_code == 201)


def test_update_customer(requests_mock):

    requests_mock.put(urljoin(test_server_url, "{}{}/".format(customer.base_url, customer_id)), status_code=200, json=json_data)

    response_update_customer = customer.update_customer(1, json_data)

    assert(response_update_customer.json() == json_data)
    assert(response_update_customer.status_code == 200)
