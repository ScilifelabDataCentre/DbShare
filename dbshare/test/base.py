"Base class for tests."

import json
import os
import unittest

import jsonschema
import requests

CONFIG = {
    "base_url": "http://127.0.0.1:5000", # DbShare server base url
    "username": None,           # Needs to be set! Must have admin privileges.
    "apikey": None,             # Needs to be set! For the above user.
    "filename": "/tmp/test.sqlite3", # Sqlite3 file
    "dbname": "test",
    "tablename": "t1"
}

with open('config.json') as infile:
    CONFIG.update(json.load(infile))

# Add API root url
CONFIG['root_url'] = CONFIG['base_url'] + '/api'


class Base(unittest.TestCase):

    def setUp(self):
        self.session = requests.Session()
        self.session.headers.update({'x-apikey': CONFIG['apikey']})

    def delete_file(self):
        try:
            os.remove(CONFIG['filename'])
        except OSError:
            pass
