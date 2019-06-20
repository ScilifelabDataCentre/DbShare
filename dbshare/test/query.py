"Test the query API endpoint."

import http.client

import base


class Query(base.Base):
    "Test the query API endpoint."

    def setUp(self):
        "Upload a file containing a plain Sqlite3 database."
        super().setUp()
        self.upload_file()
        self.assertEqual(self.root['operations']['database']['query']['method'], 'POST')
        self.assertTrue('variables' in self.root['operations']['database']['query'])
        url = self.root['operations']['database']['query']['href']
        self.url_query = url.format(dbname=base.CONFIG['dbname'])

    def test_table_query_one_column(self):
        "Get only one column from the test table."
        query = {'select': 't',
                 'from': 't1'}
        response = self.session.post(self.url_query, json=query)
        result = self.check_schema(response)

        # Check correct results.
        self.assertEqual(result['nrows'], len(result['data']))
        self.assertEqual(len(result['data'][0]), 1)

    def test_table_query_three_columns(self):
        "Get all columns, there are 3 in the test table."
        query = {'select': '*',
                 'from': 't1'}
        response = self.session.post(self.url_query, json=query)
        result = self.check_schema(response)

        # Check correct results.
        self.assertEqual(result['nrows'], len(result['data']))
        self.assertEqual(len(result['data'][0]), 3)

    def test_table_query_bad(self):
        "A bad query should yield HTTP Bad Request."
        query = {'select': None,
                 'from': 't1'}
        response = self.session.post(self.url_query, json=query)
        self.assertEqual(response.status_code, http.client.BAD_REQUEST)

    def test_table_query_rename_column(self):
        "A different result column name."
        name = 'weird-column:name'
        query = {'select': f't as "{name}"',
                 'from': 't1'}
        response = self.session.post(self.url_query, json=query)
        result = self.check_schema(response)

        # Check correct results.
        self.assertEqual(result['nrows'], len(result['data']))
        self.assertEqual(len(result['data'][0]), 1)
        self.assertEqual(list(result['data'][0].keys()), [name])

    def test_table_query_limit(self):
        "Limit to 2 rows."
        query = {'select': 't',
                 'from': 't1',
                 'limit': 2}
        response = self.session.post(self.url_query, json=query)
        result = self.check_schema(response)

        # Check correct results.
        self.assertEqual(result['nrows'], len(result['data']))
        self.assertEqual(result['nrows'], 2)
        self.assertEqual(len(result['data'][0]), 1)


if __name__ == '__main__':
    base.run()
