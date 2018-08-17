import os
# Python3
try:
    from urllib.parse import urljoin
# Python2
except ImportError:
    from urlparse import urljoin

from sflvault.users.account import Account

test_server_url = os.getenv("VAULT_SERVER")
json_data = '{"id":1,"department":"test","pubkey":"123","user":2,"groups":[]}'
account = Account()
account_id = 1


def test_get_account_list(requests_mock):
    requests_mock.get(urljoin(test_server_url, account.base_url), json=json_data)

    response_get_account_list = account.get_account_list()

    assert(response_get_account_list.json() == json_data)
    assert(response_get_account_list.status_code == 200)


def test_get_single_account(requests_mock):
    requests_mock.get(urljoin(test_server_url, "{}{}/".format(account.base_url, account_id)), json=json_data)

    response_get_single_account = account.get_single_account(account_id)

    assert(response_get_single_account.json() == json_data)
    assert(response_get_single_account.status_code == 200)


def test_update_account(requests_mock):
    requests_mock.put(urljoin(test_server_url, "{}{}/".format(account.base_url, account_id)), json=json_data)

    response_update_account = account.update_account(account_id, json_data)

    assert(response_update_account.json() == json_data)
    assert(response_update_account.status_code == 200)


def test_delete_account(requests_mock):
    requests_mock.delete(urljoin(test_server_url, "{}{}/".format(account.base_url, account_id)), status_code=204)

    response_delete_account = account.delete_account(account_id)

    assert(response_delete_account.status_code == 204)


def test_new_account(requests_mock):
    requests_mock.post(urljoin(test_server_url, account.base_url), json=json_data, status_code=201)

    response_new_account = account.new_account(json_data)

    assert(response_new_account.json() == json_data)
    assert(response_new_account.status_code == 201)
