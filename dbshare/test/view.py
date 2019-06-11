"Test the view API endpoint."

import http.client

import dbshare.schema.db
import dbshare.schema.view
import dbshare.schema.rows

from dbshare.test.base import *


class View(Base):
    "Test the view API endpoint."

    def setUp(self):
        "Upload a file containing a plain Sqlite3 database."
        super().setUp()
        self.upload_file()

    def test_db_upload(self):
        "Create a database with view by file upload, check the view JSON."

        # Valid API view JSON.
        response = self.session.get(URL('view', CONFIG['dbname'], 'v1'))
        self.assertEqual(response.status_code, http.client.OK)
        result = response.json()
        json_validate(result, dbshare.schema.view.schema)
        rows_url = result['rows']['href']

        # Valid API view rows JSON.
        response = self.session.get(rows_url)
        self.assertEqual(response.status_code, http.client.OK)
        json_validate(response.json(), dbshare.schema.rows.schema)


if __name__ == '__main__':
    run()
