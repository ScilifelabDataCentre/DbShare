"Test the db API endpoint."

import http.client
import sqlite3

import base


class Db(base.Base):
    "Test the db API endpoint."

    def test_create(self):
        "Create an empty database, check its JSON, and delete it."

        # Create empty database, validate database JSON.
        response = self.create_database()
        self.assertEqual(response.status_code, http.client.OK)
        self.check_schema(response)

        # Attempt at creating the database again should fail.
        response = self.session.put(self.db_url)
        self.assertEqual(response.status_code, http.client.FORBIDDEN)
        result = response.json()
        self.assertEqual(result.get('message'), 'database exists')

        # Delete the database.
        response = self.session.delete(self.db_url)
        self.assertEqual(response.status_code, http.client.NO_CONTENT)

    def test_upload(self):
        "Create a database by file upload, check its JSON."
        response = self.upload_file()
        self.assertEqual(response.status_code, http.client.OK)
        self.check_schema(response)

    def test_bad_upload(self):
        "Try uploading with the wrong content type."
        dbops = self.root['operations']['database']
        url = dbops['create']['href'].format(dbname=base.CONFIG['dbname'])
        headers = {'Content-Type': 'application/garbage'}
        response = self.session.put(url, data='garbage', headers=headers)
        self.assertEqual(response.status_code,
                         http.client.UNSUPPORTED_MEDIA_TYPE)

    def test_edit(self):
        "Create an empty database, edit it, check its JSON."

        # Create empty database.
        response = self.create_database()
        self.assertEqual(response.status_code, http.client.OK)
        self.check_schema(response)

        # Edit the title.
        title = 'New title'
        response = self.session.post(self.db_url, json={'title': title})
        self.assertEqual(response.status_code, http.client.OK)
        result = self.check_schema(response)
        self.assertEqual(result.get('title'), title)

        # Edit the description.
        description = 'A description'
        response = self.session.post(self.db_url,
                                     json={'description': description})
        self.assertEqual(response.status_code, http.client.OK)
        result = self.check_schema(response)
        # Updated description.
        self.assertEqual(result.get('description'), description)
        # Same title as before.
        self.assertEqual(result.get('title'), title)

        # Rename the database; record its new url.
        name = 'test2'
        response = self.session.post(self.db_url, json={'name': name})
        self.assertEqual(response.status_code, http.client.OK)
        result = self.check_schema(response)
        self.assertTrue(result['$id'].endswith(name))

        # So that the database is deleted at cleanup.
        self.db_url = result['$id']

    def test_readonly(self):
        "Create an empty database, set to read-only, then read-write."

        # Create empty database.
        response = self.create_database()
        self.assertEqual(response.status_code, http.client.OK)

        # Set to read-only, validate JSON.
        response = self.session.post(f"{self.db_url}/readonly")
        self.assertEqual(response.status_code, http.client.OK)
        result = self.check_schema(response)

        # Check items that must exist.
        self.assertTrue(result['readonly'])
        self.assertTrue(result['hashes'])

        # Try editing the database; should fail.
        title = 'New title'
        response = self.session.post(self.db_url, json={'title': title})
        self.assertEqual(response.status_code, http.client.UNAUTHORIZED)

        # Set to read-write, validate JSON.
        response = self.session.post(f"{self.db_url}/readwrite")
        self.assertEqual(response.status_code, http.client.OK)
        result = self.check_schema(response)

        # Check items must no longer exist.
        self.assertFalse(result['readonly'])
        self.assertFalse(result['hashes'])


if __name__ == '__main__':
    base.run()
