"Base class for tests."

import argparse
import http.client
import json
import os
import re
import sqlite3
import sys
import unittest
import urllib

import jsonschema
import requests

SCHEMA_LINK_RX = re.compile(r'<([^>])+>; rel="([^"]+)')

JSON_MIMETYPE    = 'application/json'

DEFAULT_CONFIG = {
    'base_url': 'http://127.0.0.1:5000', # DbShare server base url.
    'base_schema': None,        # Use schema from server at base url.
    'username': None,           # Needs to be set! Must have admin privileges.
    'apikey': None,             # Needs to be set! For the above user.
    'filename': '/tmp/test.sqlite3', # Sqlite3 file
    'dbname': 'test'
}

# The actual configuration values to use.
CONFIG = {}

def process_args(filepath=None):
    """Process command-line arguments for this test suite.
    Reset the configuration and read the given configuration file.
    Return the unused arguments.
    """
    if filepath is None:
        parser = argparse.ArgumentParser()
        parser.add_argument('-C', '--config', dest='config',
                            metavar='FILE', default='config.json',
                            help='Configuration file')
        parser.add_argument('unittest_args', nargs='*')
        options, args = parser.parse_known_args()
        filepath = options.config
        args = [sys.argv[0]] + args
    else:
        args = sys.argv
    CONFIG.update(DEFAULT_CONFIG)
    with open(filepath) as infile:
        CONFIG.update(json.load(infile))
    # Add API root url.
    CONFIG['root_url'] = CONFIG['base_url'] + '/api'
    return args

def run():
    unittest.main(argv=process_args())


class Base(unittest.TestCase):
    "Base class for DbShare test cases."

    def setUp(self):
        self.schemas = {}
        self.session = requests.Session()
        self.session.headers.update({'x-apikey': CONFIG['apikey']})
        self.addCleanup(self.close_session)

    def close_session(self):
        self.session.close()

    @property
    def root(self):
        "Return the API root data."
        try:
            return self._root
        except AttributeError:
            response = self.session.get(CONFIG['root_url'])
            self.assertEqual(response.status_code, http.client.OK)
            self.check_schema(response)
            self._root = response.json()
            return self._root

    def check_schema(self, response):
        """Check that there is a schema linked in the response headers,
        and that the response JSON data matches that schema.
        Return the response JSON.
        """
        self.assertEqual(response.status_code, http.client.OK)
        url = response.links['schema']['url']
        # Change to the local schema, rather than the default remote global.
        if CONFIG['base_schema']:
            b = urllib.parse.urlparse(CONFIG['base_url'])
            s = urllib.parse.urlparse(url)
            s = s._replace(scheme=b.scheme, netloc=b.netloc)
            url = s.geturl()
        try:
            schema = self.schemas[url]
        except KeyError:
            r = self.session.get(url)
            self.assertEqual(r.status_code, http.client.OK)
            schema = r.json()
            self.schemas[url] = schema
        result = response.json()
        self.validate_schema(result, schema)
        return result

    def validate_schema(self, instance, schema):
        "Validate the JSON instance versus the given JSON schema."
        jsonschema.validate(instance=instance,
                            schema=schema,
                            format_checker=jsonschema.draft7_format_checker)

    def create_database(self):
        "Create an empty database."
        dbops = self.root['operations']['database']
        self.assertTrue('variables' in dbops['create'])
        self.assertTrue('dbname' in dbops['create']['variables'])
        url = dbops['create']['href'].format(dbname=CONFIG['dbname'])
        response = self.session.put(url)
        self.assertEqual(response.status_code, http.client.OK)
        self.db_url = response.url
        self.addCleanup(self.delete_db)
        return response

    def upload_file(self):
        "Create a local Sqlite3 file and upload it."
        # Create the database in a local file.
        cnx = sqlite3.connect(CONFIG['filename'])
        self.addCleanup(self.delete_file)
        # Create a table in the database.
        cnx.execute("CREATE TABLE t1 ("
                    "i INTEGER PRIMARY KEY,"
                    "r REAL,"
                    "t TEXT NOT NULL)")
        cnx.execute(f"CREATE VIEW v1"
                    f" AS SELECT r, t FROM t1"
                    " WHERE i>=2")
        with cnx:
            cnx.execute("INSERT INTO t1 (i,r,t)"
                        " VALUES (?,?,?)", (1, 2.1, 'a'))
            cnx.execute("INSERT INTO t1 (i,r,t)"
                        " VALUES (?,?,?)", (2, 0.5, 'b'))
            cnx.execute("INSERT INTO t1 (i,r,t)"
                        " VALUES (?,?,?)", (3, -1.5, 'c'))
        cnx.close()
        # Upload the database file.
        dbops = self.root['operations']['database']
        url = dbops['create']['href'].format(dbname=CONFIG['dbname'])
        with open(CONFIG['filename'], 'rb') as infile:
            response = self.session.put(url, data=infile)
            self.assertEqual(response.status_code, http.client.OK)
            self.db_url = response.url
        self.addCleanup(self.delete_db)
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
