import tempfile

import pytest

from sflvault.config.config import Config


@pytest.fixture
def config_fixture():
    tf = tempfile.NamedTemporaryFile(dir='tests/data')

    yaml_data = "test: test"

    with open(tf.name, 'w') as f:
        f.write(yaml_data)

    config = Config(tf.name)
    yield config

    # TearDown
    tf.close()


def test_config_not_found():
    with pytest.raises(IOError):
        config_not_found = Config("1234")


def test_get_config_key_value(config_fixture):
    value = config_fixture.get('test')
    assert(value == 'test')


def test_get_config_key_none(config_fixture):
    with pytest.raises(KeyError):
        config_fixture.get('key_doesnt_exist')


def test_save_config(config_fixture):

    config_fixture.set('test1', 'test1')
    value = config_fixture.get('test1')

    assert(value == 'test1')
