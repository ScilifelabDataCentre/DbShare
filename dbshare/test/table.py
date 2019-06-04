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
        "Create a database and a table in it. Check its definition."

        # Create an empty database.
        response = self.create_database()
        self.assertEqual(response.status_code, http.client.OK)

        # Create a table in the database.
        url = f"{CONFIG['root_url']}/table/{CONFIG['dbname']}/{self.table_spec['name']}"
        response = self.session.put(url, json=self.table_spec)
        self.assertEqual(response.status_code, http.client.OK)

        # Check the created table against the spec.
        data = response.json()
        jsonschema.validate(instance=data,
                            schema=dbshare.schema.table.schema)
        self.assertEqual(len(data['columns']), len(self.table_spec['columns']))
        self.assertEqual(data['title'], self.table_spec['title'])
        lookup = dict([(c['name'], c) for c in self.table_spec['columns']])
        for column in data['columns']:
            self.assertTrue(column['name'] in lookup)
            self.assertEqual(column['type'], lookup[column['name']]['type'])

        # PRIMAY KEY implies NOT NULL.
        lookup = dict([(c['name'], c) for c in data['columns']])
        self.assertTrue(lookup['i']['primarykey'])
        self.assertTrue(lookup['i']['notnull'])


if __name__ == '__main__':
    run()
