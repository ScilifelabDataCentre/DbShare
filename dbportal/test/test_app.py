"Test DbPortal API; top level."

import json
import unittest

import jsonschema
import requests

import dbportal.schema.root


CONFIG = {"root": "http://127.0.0.1:5000/api"}

# The config file must contain 'apikey' for an admin user.
with open('config.json') as infile:
    CONFIG.update(json.load(infile))


class App(unittest.TestCase):
    "Test the DbPortal API root."

    def setUp(self):
        self.session = requests.Session()
        self.session.headers.update({'x-apikey': CONFIG['apikey']})

    def test_access(self):
        "Test access to the API root."
        response = self.session.get(CONFIG['root'])
        self.assertEqual(response.status_code, 200)

    def test_redirect(self):
        "Test redirect to the API root from HTML home page."
        url = CONFIG['root'].strip('/api')
        response = self.session.get(url, headers={'Accept': 'application/json'})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.url, CONFIG['root'])

    def test_schema(self):
        "Test validity of the API root JSON."
        response = self.session.get(CONFIG['root'])
        self.assertEqual(response.status_code, 200)
        jsonschema.validate(instance=response.json(),
                            schema=dbportal.schema.root.schema)


if __name__ == '__main__':
    unittest.main()
