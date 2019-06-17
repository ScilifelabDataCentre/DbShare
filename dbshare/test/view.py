"Test the view API endpoint."

import http.client

import base


class View(base.Base):
    "Test the view API endpoint."

    def setUp(self):
        "Upload a file containing a plain Sqlite3 database."
        super().setUp()
        self.upload_file()

    def test_db_upload(self):
        "Create a database with view by file upload, check the view JSON."

        # Valid view JSON.
        response = self.session.get(base.url('view', 
                                             base.CONFIG['dbname'], 
                                             'v1'))
        self.assertEqual(response.status_code, http.client.OK)
        result = response.json()
        schema = self.get_schema(response)
        self.assertTrue(schema is not None)
        base.json_validate(result, schema)

        # Valid view rows JSON.
        rows_url = result['rows']['href']
        response = self.session.get(rows_url)
        self.assertEqual(response.status_code, http.client.OK)
        result = response.json()
        schema = self.get_schema(response)
        self.assertTrue(schema is not None)
        base.json_validate(result, schema)


if __name__ == '__main__':
    base.run()
