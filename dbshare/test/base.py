"Base class for tests."

import json
import unittest

import jsonschema
import requests

CONFIG = {"root": "http://127.0.0.1:5000/api"}

# The config file must contain 'apikey' for an admin user.
with open('config.json') as infile:
    CONFIG.update(json.load(infile))


class Base(unittest.TestCase):

    def setUp(self):
        self.session = requests.Session()
        self.session.headers.update({'x-apikey': CONFIG['apikey']})
