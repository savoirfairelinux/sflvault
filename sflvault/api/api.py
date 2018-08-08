import requests


class APIHandler:

    def __init__(self, hostname):
        self.hostname = hostname

    def get(self, endpoint):
        url = self.hostname + endpoint
        return requests.get(url)

    def post(self, endpoint, data):
        url = self.hostname + endpoint
        return requests.post(url, data)

    def put(self, endpoint, data):
        url = self.hostname + endpoint
        return requests.put(url, data)

    def delete(self, endpoint):
        url = self.hostname + endpoint
        return requests.delete(url)
