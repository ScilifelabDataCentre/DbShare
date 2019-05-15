"Test the DbShare API table endpoint."

import http.client
import os
import sqlite3

import dbshare.schema.table

from dbshare.test.base import *

DBNAME = 'test'
TABLENAME = 't1'

class Table(Base):
    "Test the DbShare API table endpoint."

    def setUp(self):
        url = f"{CONFIG['root']}/db/{DBNAME}"
        # Ensure that no such database exists.
        self.session.delete(url)
        response = self.session.put(url)
        self.assertEqual(response.status_code, http.client.OK)

    def tearDown(self):
        url = f"{CONFIG['root']}/db/{DBNAME}"
        self.session.delete(url)

    def test_table_create(self):
        pass
