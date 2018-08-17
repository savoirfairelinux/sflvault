import os
# Python3
try:
    from urllib.parse import urljoin
# Python2
except ImportError:
    from urlparse import urljoin

from sflvault.users.account_group import AccountGroup

test_server_url = os.getenv("VAULT_SERVER")
json_data = '{"id":1,"name":"Test Group","is_hidden":false,"pubkey":"123"}'
account_group = AccountGroup()
account_group_id = 1


def test_get_account_group_list(requests_mock):
    requests_mock.get(urljoin(test_server_url, account_group.base_url), json=json_data)

    response_get_account_group_list = account_group.get_account_group_list()

    assert(response_get_account_group_list.json() == json_data)
    assert(response_get_account_group_list.status_code == 200)


def test_get_single_account_group(requests_mock):
    requests_mock.get(urljoin(test_server_url, "{}{}/".format(account_group.base_url, account_group_id)), json=json_data)

    response_get_account_group_list = account_group.get_single_account_group(account_group_id)

    assert(response_get_account_group_list.json() == json_data)
    assert(response_get_account_group_list.status_code == 200)


def test_update_account_group(requests_mock):
    requests_mock.put(urljoin(test_server_url, "{}{}/".format(account_group.base_url, account_group_id)), json=json_data, status_code=201)

    response_update_account_group = account_group.update_account_group(account_group_id, json_data)

    assert(response_update_account_group.json() == json_data)
    assert(response_update_account_group.status_code == 201)


def test_delete_account_group(requests_mock):
    requests_mock.delete(urljoin(test_server_url, "{}{}/".format(account_group.base_url, account_group_id)), status_code=204)

    response_delete_account_group = account_group.delete_account_group(account_group_id)

    assert(response_delete_account_group.status_code == 204)


def test_new_account_group(requests_mock):
    requests_mock.post(urljoin(test_server_url, account_group.base_url), json=json_data, status_code=201)

    response_new_account_group = account_group.new_account_group(json_data)

    assert(response_new_account_group.json() == json_data)
    assert(response_new_account_group.status_code == 201)
