"Test the view API endpoint."

import http.client

import base


class View(base.Base):
    "Test the view API endpoint."

    def setUp(self):
        "Upload a file containing a plain Sqlite3 database."
        super().setUp()
        response = self.upload_file()
        result = self.check_schema(response)
        self.url_view = result['views'][0]['href']

    def test_db_upload(self):
        "Create a database with view by file upload, check the view JSON."
        response = self.session.get(self.url_view)
        result = self.check_schema(response)
        url = result['rows']['href']
        response = self.session.get(url)
        result = self.check_schema(response)
        self.assertEqual(result['nrows'], 2)
        self.assertEqual(len(result['data']), 2)


if __name__ == '__main__':
    base.run()
