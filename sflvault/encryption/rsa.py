from sflvault.encryption.base import BaseEncryption
from Cryptodome.PublicKey import RSA


class RSAKey(BaseEncryption):

    def __init__(self):

        try:
            self.rsa_pub_key_location = self.config.get("RSA_PUBLIC_KEY")
            self.rsa_private_key_location = self.config.get("RSA_PRIVATE_KEY")
        except KeyError as e:
            print(e)

        super(BaseEncryption, self).__init__()

    def encrypt(self):
        pass

    def decrypt(self):
        pass

    def validate(self):
        pass

    def sign(self):
        pass

    def import_key(self, key_file):
        return RSA.importKey(key_file)

    def generate_new_key(self, bits=2048):
        return RSA.generate(bits)

    def _export_key(self, private_key, public_key):
        pass
