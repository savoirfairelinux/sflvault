import yaml


class Config():

    def __init__(self, path):
        self.default_config_location = path
        try:
            with open(self.default_config_location, 'r') as f:
                self.config = yaml.safe_load(f)
        except IOError as e:
            e.args += (path,)
            raise

    def get(self, key):
        try:
            return self.config[key]
        except KeyError as e:
            e.args += (key,)
            raise

    def set(self, key, value):
        self.config[key] = value
        self._save_config()

    def _save_config(self):
        try:
            with open(self.default_config_location, 'w') as f:
                yaml.safe_dump(self.config, f)
        except IOError as e:
            e.args += (self.default_config_location,)
            raise
