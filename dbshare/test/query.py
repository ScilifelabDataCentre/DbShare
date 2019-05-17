"Test the query API endpoint."

import http.client

import dbshare.schema.db
import dbshare.schema.table
import dbshare.schema.query

from dbshare.test.base import *


class Query(Base):
    "Test the DbShare API table endpoint."

    def test_table_query(self):
        "Test a query on a table in a database."

        # Upload a file containing a plain Sqlite3 database.
        response = self.upload_file()
        self.assertEqual(response.status_code, http.client.OK)

        # Get only one column from the test table.
        query = {'select': 't',
                 'from': CONFIG['tablename']}
        url = f"{CONFIG['root_url']}/query/{CONFIG['dbname']}"
        response = self.session.get(url, json=query)
        self.assertEqual(response.status_code, http.client.OK)
        result = response.json()
        jsonschema.validate(instance=result,
                            schema=dbshare.schema.query.schema)
        self.assertEqual(result['nrows'], len(result['data']))
        self.assertEqual(len(result['data'][0]), 1)

        # Get all columns, there are 3 in the test table.
        query = {'select': '*',
                 'from': CONFIG['tablename']}
        url = f"{CONFIG['root_url']}/query/{CONFIG['dbname']}"
        response = self.session.get(url, json=query)
        self.assertEqual(response.status_code, http.client.OK)
        result = response.json()
        jsonschema.validate(instance=result,
                            schema=dbshare.schema.query.schema)
        self.assertEqual(result['nrows'], len(result['data']))
        self.assertEqual(len(result['data'][0]), 3)

        # A bad query should yield HTTP Bad Request
        query = {'select': None,
                 'from': CONFIG['tablename']}
        url = f"{CONFIG['root_url']}/query/{CONFIG['dbname']}"
        response = self.session.get(url, json=query)
        self.assertEqual(response.status_code, http.client.BAD_REQUEST)


if __name__ == '__main__':
    unittest.main()
                 
