from sflvault.encryption.base import BaseEncryption

def test_encryption_base_class():
    def create_mock_config():
        return {'test': 'test'}

    encryption = BaseEncryption(create_mock_config)
    assert(encryption is not None)
