from sflvault.api.api import APIHandler


def test_api_instance():
    api = APIHandler('localhost')

    assert api.hostname == 'localhost'


def test_api_get(requests_mock):
    api = APIHandler('http://vault.server')

    requests_mock.get('http://vault.server/test', json="{test: test}")

    response_get = api.get('/test')
    assert(response_get.json() == "{test: test}")
    assert(response_get.status_code == 200)


def test_api_post(requests_mock):
    api = APIHandler('http://vault.server')

    requests_mock.post('http://vault.server/test_post', json="{test: test}", status_code=201)

    response_post = api.post('/test_post', {})
    assert(response_post.json() == "{test: test}")
    assert(response_post.status_code == 201)


def test_api_delete(requests_mock):
    api = APIHandler('http://vault.server')

    requests_mock.delete('http://vault.server/test_delete', json="{test: test}", status_code=204)

    response_delete = api.delete('/test_delete')
    assert(response_delete.json() == "{test: test}")
    assert(response_delete.status_code == 204)


def test_api_put(requests_mock):
    api = APIHandler('http://vault.server')

    requests_mock.put('http://vault.server/test_put', json="{test: test}", status_code=200)

    response_put = api.put('/test_put', {})
    assert(response_put.json() == "{test: test}")
    assert(response_put.status_code == 200)
