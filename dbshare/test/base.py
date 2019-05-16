"Base class for tests."

import http.client
import json
import os
import sqlite3
import unittest

import jsonschema
import requests

CONFIG = {
    'base_url': 'http://127.0.0.1:5000', # DbShare server base url
    'username': None,           # Needs to be set! Must have admin privileges.
    'apikey': None,             # Needs to be set! For the above user.
    'filename': '/tmp/test.sqlite3', # Sqlite3 file
    'dbname': 'test',
    'tablename': 't1',
    'viewname': 'v1'
}

with open('config.json') as infile:
    CONFIG.update(json.load(infile))

# Add API root url
CONFIG['root_url'] = CONFIG['base_url'] + '/api'


class Base(unittest.TestCase):

    def setUp(self):
        self.session = requests.Session()
        self.session.headers.update({'x-apikey': CONFIG['apikey']})

    def upload_file(self, view=False):
        "Create a local Sqlite3 file and upload it."
        # Define the URL for the database.
        self.db_url = f"{CONFIG['root_url']}/db/{CONFIG['dbname']}"
        # Create the database in a local file.
        cnx = sqlite3.connect(CONFIG['filename'])
        self.addCleanup(self.delete_file)
        # Create a table in the database.
        cnx.execute(f"CREATE TABLE {CONFIG['tablename']} ("
                    "i INTEGER PRIMARY KEY,"
                    "r REAL,"
                    "t TEXT NOT NULL)")
        with cnx:
            cnx.execute(f"INSERT INTO {CONFIG['tablename']} (i,r,t)"
                        " VALUES (?,?,?)", (1, 2.1, 'a'))
            cnx.execute(f"INSERT INTO {CONFIG['tablename']} (i,r,t)"
                        " VALUES (?,?,?)", (2, 0.5, 'b'))
            cnx.execute(f"INSERT INTO {CONFIG['tablename']} (i,r,t)"
                        " VALUES (?,?,?)", (3, -1.5, 'c'))
        if view:
            cnx.execute(f"CREATE VIEW {CONFIG['viewname']}"
                        f" AS SELECT r, t FROM {CONFIG['tablename']}"
                        " WHERE i>=2")
        cnx.close()
        # Upload the database file.
        with open(CONFIG['filename'], 'rb') as infile:
            response = self.session.put(self.db_url, data=infile)
        self.addCleanup(self.delete_db)
        self.assertEqual(response.status_code, http.client.OK)
        return response

    def delete_file(self):
        try:
            os.remove(CONFIG['filename'])
        except OSError:
            pass

    def delete_db(self):
        try:
            self.session.delete(self.db_url)
        except AttributeError:
            pass
