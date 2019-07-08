"Test the table API endpoint."

import copy
import csv
import io
import http.client

import base


class Table(base.Base):
    "Test the table API endpoint."

    table_spec = {
        'name': 't1',
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

    def get_csvfile_data(self, rows):
        csvfile = io.StringIO()
        writer = csv.writer(csvfile, delimiter=',')
        writer.writerow([c['name'] for c in self.table_spec['columns']])
        writer.writerows(rows)
        return csvfile.getvalue()

    def test_db_upload(self):
        "Create a database with table by file upload, check the table JSON."
        response = self.upload_file()
        result = self.check_schema(response)

        # Check contents of table JSON.
        self.assertEqual(len(result['tables']), 1)
        self.assertEqual(len(result['views']), 1)
        table_url = result['tables'][0]['href']
        self.assertEqual(result['tables'][0]['nrows'], 3)
        rows_url = result['tables'][0]['rows']['href']

        # Validate the table API JSON.
        response = self.session.get(table_url)
        result = self.check_schema(response)
        self.assertEqual(result['rows']['href'], rows_url)

        # Validate the table rows JSON, and content.
        response = self.session.get(rows_url)
        result = self.check_schema(response)
        self.assertEqual(result['nrows'], 3)
        self.assertEqual(result['nrows'], len(result['data']))

        # Content negotiation for rows using URL without '.json' extension.
        response = self.session.get(rows_url.rstrip('.json'),
                                    headers={'Accept': base.JSON_MIMETYPE})
        self.check_schema(response)

    def test_create(self):
        "Create a database and a table in it. Check the table definition."

        # Create an empty database.
        response = self.create_database()
        result = self.check_schema(response)

        # Create a table in the database.
        url = self.root['operations']['table']['create']['href']
        url = url.format(dbname=base.CONFIG['dbname'],
                         tablename=self.table_spec['name'])
        response = self.session.put(url, json=self.table_spec)
        result = self.check_schema(response)

        # Check the created table.
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

    def test_name_clash(self):
        "Try creating a table with uppercase name of already existing."

        # Create an empty database.
        response = self.create_database()
        result = self.check_schema(response)

        # Create a table in the database.
        url = self.root['operations']['table']['create']['href']
        url = url.format(dbname=base.CONFIG['dbname'],
                         tablename=self.table_spec['name'])
        response = self.session.put(url, json=self.table_spec)
        result = self.check_schema(response)

        # Try creating same table but with upper-case name.
        table_spec = copy.deepcopy(self.table_spec)
        table_spec['name'] = table_spec['name'].upper()
        url = self.root['operations']['table']['create']['href']
        url = url.format(dbname=base.CONFIG['dbname'],
                         tablename=table_spec['name'])
        response = self.session.put(url, json=table_spec)
        self.assertEqual(response.status_code, http.client.BAD_REQUEST)

    def test_insert(self):
        "Create database and table; insert data."

        # Create an empty database.
        response = self.create_database()
        result = self.check_schema(response)

        # Create a table in the database.
        url = self.root['operations']['table']['create']['href']
        url = url.format(dbname=base.CONFIG['dbname'],
                         tablename=self.table_spec['name'])
        response = self.session.put(url, json=self.table_spec)
        result = self.check_schema(response)
        url_table = response.url
        result = self.check_schema(response)
        self.assertEqual(result['nrows'], 0)

        # Insert data.
        url = self.root['operations']['table']['insert']['href']
        url = url.format(dbname=base.CONFIG['dbname'],
                         tablename=self.table_spec['name'])
        data = {'data': [{'i': 1, 't': 'stuff', 'r': 1.2345}] }
        response = self.session.post(url, json=data)
        result = self.check_schema(response)
        self.assertEqual(result['nrows'], 1)

        data = {'data': [{'i': 2, 't': 'another', 'r': 3}] }
        response = self.session.post(url, json=data)
        self.assertEqual(response.status_code, http.client.OK)
        result = response.json()
        self.assertEqual(result['nrows'], 2)

        data = {'data': [{'i': 3, 'r': -0.45}] }
        response = self.session.post(url, json=data)
        self.assertEqual(response.status_code, http.client.OK)
        result = response.json()
        self.assertEqual(result['nrows'], 3)

        row_3 = {'i': 4, 't': 'multirow', 'r': -0.45}
        data = {'data': [row_3,
                         {'i': 5, 't': 'multirow 2', 'r': 1.2e4}] }
        response = self.session.post(url, json=data)
        self.assertEqual(response.status_code, http.client.OK)
        result = response.json()
        self.assertEqual(result['nrows'], 5)

        # Try to insert invalid data of different kinds.
        data = {'data': [{'i': 3, 't': 'primary key clash', 'r': -0.1}] }
        response = self.session.post(url, json=data)
        self.assertEqual(response.status_code, http.client.BAD_REQUEST)

        data = {'data': [{'i': 8, 't': 'missing value'}] }
        response = self.session.post(url, json=data)
        self.assertEqual(response.status_code, http.client.BAD_REQUEST)

        data = {'data': [{'i': 9, 't': 'wrong type', 'r': 'string!'}] }
        response = self.session.post(url, json=data)
        self.assertEqual(response.status_code, http.client.BAD_REQUEST)

        # Get the table data.
        response = self.session.get(url_table)
        self.assertEqual(response.status_code, http.client.OK)
        result = response.json()
        self.assertEqual(result['nrows'], 5)

        # Get the rows and compare one of them
        url = result['rows']['href']
        response = self.session.get(url)
        result = self.check_schema(response)
        self.assertEqual(result['nrows'], 5)
        self.assertEqual(len(result['data']), result['nrows'])
        self.assertEqual(result['data'][3], row_3)

        # Empty the table.
        url = self.root['operations']['table']['empty']['href']
        url = url.format(dbname=base.CONFIG['dbname'],
                         tablename=self.table_spec['name'])
        response = self.session.post(url)
        self.assertEqual(response.status_code, http.client.OK)
        response = self.session.get(response.url)
        result = self.check_schema(response)
        self.assertEqual(result['nrows'], 0)

    def test_csv(self):
        "Create database and table; insert CSV operations."

        # Create an empty database.
        response = self.create_database()
        result = self.check_schema(response)

        # Create a table in the database.
        url = self.root['operations']['table']['create']['href']
        url = url.format(dbname=base.CONFIG['dbname'],
                         tablename=self.table_spec['name'])
        response = self.session.put(url, json=self.table_spec)
        result = self.check_schema(response)
        self.assertEqual(result['nrows'], 0)

        headers = {'Content-Type': 'text/csv'}

        # Insert CSV data.
        url = self.root['operations']['table']['insert']['href']
        url = url.format(dbname=base.CONFIG['dbname'],
                         tablename=self.table_spec['name'])
        data = self.get_csvfile_data([(1, 'test', 0.2),
                                      (2, 'another test', 4.123e5),
                                      (3, 'third', -13)])
        response = self.session.post(url, data=data, headers=headers)
        result = self.check_schema(response)
        self.assertEqual(result['nrows'], 3)

        # Row with None for a pkey item.
        data = self.get_csvfile_data([(None, 'missing pkey', 0.2)])
        response = self.session.post(url, data=data, headers=headers)
        self.assertEqual(response.status_code, http.client.BAD_REQUEST)

        # Row with too many items.
        data = self.get_csvfile_data([(1, 'test', 2.1, 'superfluous')])
        response = self.session.post(url, data=data, headers=headers)
        self.assertEqual(response.status_code, http.client.BAD_REQUEST)

    def test_update(self):
        "Create database and table; insert and update using CSV."

        # Create an empty database.
        response = self.create_database()
        self.assertEqual(response.status_code, http.client.OK)
        result = self.check_schema(response)

        # Create a table in the database.
        url = self.root['operations']['table']['create']['href']
        url = url.format(dbname=base.CONFIG['dbname'],
                         tablename=self.table_spec['name'])
        response = self.session.put(url, json=self.table_spec)
        result = self.check_schema(response)
        self.assertEqual(result['nrows'], 0)

        # Insert CSV data.
        headers = {'Content-Type': 'text/csv'}
        url = self.root['operations']['table']['insert']['href']
        url = url.format(dbname=base.CONFIG['dbname'],
                         tablename=self.table_spec['name'])
        data = self.get_csvfile_data([(1, 'test', 0.2),
                                      (2, 'another test', 4.123e5),
                                      (3, 'third', -13)])
        response = self.session.post(url, data=data, headers=headers)
        result = self.check_schema(response)
        self.assertEqual(result['nrows'], 3)

        # Update CSV data; check that it actually changed something.
        update_url = self.root['operations']['table']['update']['href']
        update_url = update_url.format(dbname=base.CONFIG['dbname'],
                                       tablename=self.table_spec['name'])
        data = self.get_csvfile_data([(1, 'changed', -1.0)])
        response = self.session.post(update_url, data=data, headers=headers)
        result = self.check_schema(response)
        self.assertEqual(result['nrows'], 3)

        response = self.session.get(result['rows']['href'])
        result = self.check_schema(response)
        rows = result['data']
        self.assertEqual(rows[0]['i'], 1)
        self.assertEqual(rows[0]['t'], 'changed')
        self.assertEqual(rows[2]['i'], 3)
        self.assertEqual(rows[2]['t'], 'third')

        # Update non-existent row; should not change anything.
        data = self.get_csvfile_data([(4, 'this row does not exist', 1.0)])
        response = self.session.post(update_url, data=data, headers=headers)
        result = self.check_schema(response)
        self.assertEqual(result['nrows'], 3)
        response = self.session.get(result['rows']['href'])
        result = self.check_schema(response)
        self.assertEqual(rows, result['data'])

    def test_index(self):
        "Create database and table; create index and test it."

        # Create an empty database.
        response = self.create_database()
        result = self.check_schema(response)

        # Add an index definition to the table spec.
        table_spec = self.table_spec.copy()
        table_spec['indexes'] = [{'unique': True, 'columns': ['t']}]

        # Create a table in the database.
        url = self.root['operations']['table']['create']['href']
        url = url.format(dbname=base.CONFIG['dbname'],
                         tablename=table_spec['name'])
        response = self.session.put(url, json=table_spec)
        result = self.check_schema(response)
        self.assertEqual(len(result['indexes']), 1)

        # Add rows.
        headers = {'Content-Type': 'text/csv'}
        url = self.root['operations']['table']['insert']['href']
        url = url.format(dbname=base.CONFIG['dbname'],
                         tablename=self.table_spec['name'])
        data = self.get_csvfile_data([(1, 'first row', 1.0),
                                      (2, 'second row', 2.0)])
        response = self.session.post(url, data=data, headers=headers)
        result = self.check_schema(response)
        self.assertEqual(result['nrows'], 2)

        # Attempt to add rows that violates unique index.
        data = self.get_csvfile_data([(3, 'second row', 3.0)])
        response = self.session.post(url, data=data, headers=headers)
        self.assertEqual(response.status_code, http.client.BAD_REQUEST)

        # Add proper third row
        data = self.get_csvfile_data([(3, 'third row', 3.0)])
        response = self.session.post(url, data=data, headers=headers)
        result = self.check_schema(response)
        self.assertEqual(result['nrows'], 3)


if __name__ == '__main__':
    base.run()
