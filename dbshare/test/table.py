"Test the table API endpoint."

import http.client

import dbshare.schema.db
import dbshare.schema.table
import dbshare.schema.rows

from dbshare import constants
from dbshare.test.base import *


class Table(Base):
    "Test the DbShare API table endpoint."

    table_spec = {'name': 't1',
                  'title': 'Test table',
                  'columns': [
                      {'name': 'i',
                       'type': 'INTEGER',
                       'primarykey': True},
                      {'name': 't',
                       'type': 'TEXT',
                       'notnull': False},
                      {'name': 'r',
                       'type': 'REAL',
                       'notnull': True}
                  ]
    }

    def test_db_upload(self):
        "Create a database with table by file upload, check the table JSON."

        # Upload a file containing a plain Sqlite3 database.
        response = self.upload_file()
        self.assertEqual(response.status_code, http.client.OK)

        # The db API JSON is valid.
        jsonschema.validate(instance=response.json(),
                            schema=dbshare.schema.db.schema)

        # The table API JSON is valid.
        table_url = f"{CONFIG['root_url']}/table/{CONFIG['dbname']}/t1"
        response = self.session.get(table_url)
        self.assertEqual(response.status_code, http.client.OK)
        jsonschema.validate(instance=response.json(),
                            schema=dbshare.schema.table.schema)

        # The table rows JSON is valid.
        rows_url = f"{CONFIG['base_url']}/table/{CONFIG['dbname']}/t1.json"
        response = self.session.get(rows_url)
        self.assertEqual(response.status_code, http.client.OK)
        jsonschema.validate(instance=response.json(),
                            schema=dbshare.schema.rows.schema)

        # Content negotiation for rows. No '.json' extension.
        rows_url = f"{CONFIG['base_url']}/table/{CONFIG['dbname']}/t1"
        response = self.session.get(rows_url,
                                    headers={'Accept': constants.JSON_MIMETYPE})
        self.assertEqual(response.status_code, http.client.OK)
        jsonschema.validate(instance=response.json(),
                            schema=dbshare.schema.rows.schema)

    def test_create(self):
        "Create a database and a table in it. Check the table definition."

        # Create an empty database.
        response = self.create_database()
        self.assertEqual(response.status_code, http.client.OK)

        # Create a table in the database.
        url = f"{CONFIG['root_url']}/table/{CONFIG['dbname']}/{self.table_spec['name']}"
        response = self.session.put(url, json=self.table_spec)
        self.assertEqual(response.status_code, http.client.OK)

        # Check the created table against the spec.
        result = response.json()
        jsonschema.validate(instance=result,
                            schema=dbshare.schema.table.schema)
        self.assertEqual(len(result['columns']),
                         len(self.table_spec['columns']))
        self.assertEqual(result['title'], self.table_spec['title'])
        lookup = dict([(c['name'], c) for c in self.table_spec['columns']])
        for column in result['columns']:
            self.assertTrue(column['name'] in lookup)
            self.assertEqual(column['type'], lookup[column['name']]['type'])

        # PRIMAY KEY implies NOT NULL.
        lookup = dict([(c['name'], c) for c in result['columns']])
        self.assertTrue(lookup['i']['primarykey'])
        self.assertTrue(lookup['i']['notnull'])

        # Delete the table.
        response = self.session.delete(url)
        self.assertEqual(response.status_code, http.client.NO_CONTENT)

        # Check no tables in the database.
        response = self.session.get(self.db_url)
        self.assertEqual(response.status_code, http.client.OK)
        result = response.json()
        self.assertEqual(len(result['tables']), 0)

    def test_insert(self):
        "Create database and table; insert data."

        # Create an empty database.
        response = self.create_database()
        self.assertEqual(response.status_code, http.client.OK)

        # Create a table in the database.
        url = f"{CONFIG['root_url']}/table/{CONFIG['dbname']}/{self.table_spec['name']}"
        response = self.session.put(url, json=self.table_spec)
        self.assertEqual(response.status_code, http.client.OK)
        result = response.json()
        self.assertEqual(result['nrows'], 0)

        # Insert data.
        data = {'data': [{'i': 1, 't': 'stuff', 'r': 1.2345}] }
        response = self.session.post(url + '/insert', json=data)
        self.assertEqual(response.status_code, http.client.OK)
        result = response.json()
        self.assertEqual(result['nrows'], 1)

        data = {'data': [{'i': 2, 't': 'another', 'r': 3}] }
        response = self.session.post(url + '/insert', json=data)
        self.assertEqual(response.status_code, http.client.OK)
        result = response.json()
        self.assertEqual(result['nrows'], 2)

        data = {'data': [{'i': 3, 'r': -0.45}] }
        response = self.session.post(url + '/insert', json=data)
        self.assertEqual(response.status_code, http.client.OK)
        result = response.json()
        self.assertEqual(result['nrows'], 3)

        row_3 = {'i': 4, 't': 'multirow', 'r': -0.45}
        data = {'data': [row_3,
                         {'i': 5, 't': 'multirow 2', 'r': 1.2e4}] }
        response = self.session.post(url + '/insert', json=data)
        self.assertEqual(response.status_code, http.client.OK)
        result = response.json()
        self.assertEqual(result['nrows'], 5)

        # Try to insert invalid data of different kinds.
        data = {'data': [{'i': 3, 't': 'primary key clash', 'r': -0.1}] }
        response = self.session.post(url + '/insert', json=data)
        self.assertEqual(response.status_code, http.client.BAD_REQUEST)

        data = {'data': [{'i': 8, 't': 'missing value'}] }
        response = self.session.post(url + '/insert', json=data)
        self.assertEqual(response.status_code, http.client.BAD_REQUEST)

        data = {'data': [{'i': 9, 't': 'wrong type', 'r': 'string!'}] }
        response = self.session.post(url + '/insert', json=data)
        self.assertEqual(response.status_code, http.client.BAD_REQUEST)

        response = self.session.get(url)
        self.assertEqual(response.status_code, http.client.OK)
        result = response.json()
        self.assertEqual(result['nrows'], 5)

        # Get the rows and compare one of them
        response = self.session.get(result['rows']['href'])
        self.assertEqual(response.status_code, http.client.OK)
        result = response.json()
        self.assertEqual(result['nrows'], 5)
        self.assertEqual(len(result['data']), result['nrows'])
        self.assertEqual(result['data'][3], row_3)

if __name__ == '__main__':
    run()
