from feeder_utilities.exceptions import RegisterException
import json


class Register:

    def __init__(self, register_url, routing_key, requests):
        self.register_url = register_url
        self.routing_key = routing_key
        self.requests = requests

    def max_entry(self):
        response = self.requests.get(self.register_url + "/register")
        if response.status_code != 200:
            raise RegisterException("Unable to retrieve register information, response was: {}, {}".format(
                response.status_code, response.text))
        register_info = response.json()
        if 'total-entries' not in register_info:
            raise RegisterException("Register response not recognised, did not contain 'total-entries'")
        return register_info['total-entries']

    def republish_entries(self, entries):
        response = self.requests.post(self.register_url + "/entries/republish",
                                      data=json.dumps({"entries": entries, "routing_key": self.routing_key}),
                                      headers={"Content-type": "application/json", "Accept": "application/json"})
        if response.status_code != 200:
            raise RegisterException("Unable to republish enties, response was: {}, {}".format(
                response.status_code, response.text))
        return response.json()
