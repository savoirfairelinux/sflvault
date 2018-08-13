import os
# Python3
try:
    from urllib.parse import urljoin
# Python2
except ImportError:
    from urlparse import urljoin


from sflvault.api.api import APIHandler

base_url = os.getenv("VAULT_SERVER")
api = APIHandler(base_url)
test_json = "{test: test}"

test_get = 'test'
test_post = 'test_post'
test_put = 'test_put'
test_delete = 'test_delete'

def test_api_instance():

    assert api.hostname == base_url


def test_api_get(requests_mock):

    requests_mock.get(urljoin(base_url, test_get), json=test_json)

    response_get = api.get('test')
    assert(response_get.json() == test_json)
    assert(response_get.status_code == 200)


def test_api_post(requests_mock):

    requests_mock.post(urljoin(base_url, test_post), json=test_json, status_code=201)

    response_post = api.post('test_post', {})
    assert(response_post.json() == test_json)
    assert(response_post.status_code == 201)


def test_api_delete(requests_mock):

    requests_mock.delete(urljoin(base_url, test_delete), json=test_json, status_code=204)

    response_delete = api.delete('test_delete')
    assert(response_delete.json() == test_json)
    assert(response_delete.status_code == 204)


def test_api_put(requests_mock):

    requests_mock.put(urljoin(base_url, test_put), json=test_json, status_code=200)

    response_put = api.put('test_put', {})
    assert(response_put.json() == test_json)
    assert(response_put.status_code == 200)
