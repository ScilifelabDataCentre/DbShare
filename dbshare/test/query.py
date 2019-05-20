"Test the query API endpoint."

import http.client

import dbshare.schema.db
import dbshare.schema.table
import dbshare.schema.query

from dbshare.test.base import *


class Query(Base):
    "Test the DbShare API table endpoint."

    def setUp(self):
        super().setUp()
        # Upload a file containing a plain Sqlite3 database.
        self.upload_file()

    def tearDown(self):
        self.session.delete(f"{CONFIG['root_url']}/db/{CONFIG['dbname']}")
        super().tearDown()

    def test_table_query_one_column(self):
        "Get only one column from the test table."
        query = {'select': 't',
                 'from': 't1'}
        url = f"{CONFIG['root_url']}/query/{CONFIG['dbname']}"
        response = self.session.get(url, json=query)
        self.assertEqual(response.status_code, http.client.OK)
        result = response.json()
        jsonschema.validate(instance=result,
                            schema=dbshare.schema.query.schema)
        self.assertEqual(result['nrows'], len(result['data']))
        self.assertEqual(len(result['data'][0]), 1)

    def test_table_query_three_columns(self):
        "Get all columns, there are 3 in the test table."
        query = {'select': '*',
                 'from': 't1'}
        url = f"{CONFIG['root_url']}/query/{CONFIG['dbname']}"
        response = self.session.get(url, json=query)
        self.assertEqual(response.status_code, http.client.OK)
        result = response.json()
        jsonschema.validate(instance=result,
                            schema=dbshare.schema.query.schema)
        self.assertEqual(result['nrows'], len(result['data']))
        self.assertEqual(len(result['data'][0]), 3)

    def test_table_query_bad(self):
        "A bad query should yield HTTP Bad Request."
        query = {'select': None,
                 'from': 't1'}
        url = f"{CONFIG['root_url']}/query/{CONFIG['dbname']}"
        response = self.session.get(url, json=query)
        self.assertEqual(response.status_code, http.client.BAD_REQUEST)

    def test_table_query_rename_column(self):
        "A different result column name."
        name = 'weird-column:name'
        query = {'select': f't as "{name}"',
                 'from': 't1'}
        url = f"{CONFIG['root_url']}/query/{CONFIG['dbname']}"
        response = self.session.get(url, json=query)
        self.assertEqual(response.status_code, http.client.OK)
        result = response.json()
        jsonschema.validate(instance=result,
                            schema=dbshare.schema.query.schema)
        self.assertEqual(result['nrows'], len(result['data']))
        self.assertEqual(len(result['data'][0]), 1)
        self.assertEqual(list(result['data'][0].keys()), [name])

if __name__ == '__main__':
    unittest.main()
                 
