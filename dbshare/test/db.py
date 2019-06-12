"Test the db API endpoint."

import http.client
import sqlite3

import dbshare.schema.db

from dbshare.test.base import *


class Db(Base):
    "Test the db API endpoint."

    def test_create(self):
        "Create an empty database, check its JSON, and delete it."

        # Create empty database.
        response = self.create_database()
        self.assertEqual(response.status_code, http.client.OK)

        # Valid database JSON.
        json_validate(response.json(), dbshare.schema.db.output)

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

        # Upload a Sqlite3 database file.
        response = self.upload_file()
        json_validate(response.json(), dbshare.schema.db.output)

    def test_edit(self):
        "Create an empty database, edit it, check its JSON."

        # Create empty database.
        response = self.create_database()
        self.assertEqual(response.status_code, http.client.OK)

        # Valid db JSON.
        json_validate(response.json(), dbshare.schema.db.output)

        # Edit the title.
        title = 'New title'
        response = self.session.post(self.db_url, json={'title': title})
        self.assertEqual(response.status_code, http.client.OK)
        result = response.json()
        json_validate(result, dbshare.schema.db.output)
        self.assertEqual(result.get('title'), title)

        # Edit the description.
        description = 'A description'
        response = self.session.post(self.db_url,
                                     json={'description': description})
        self.assertEqual(response.status_code, http.client.OK)
        result = response.json()
        json_validate(result, dbshare.schema.db.output)
        self.assertEqual(result.get('description'), description)
        # Same title as before.
        self.assertEqual(result.get('title'), title)

        # Rename the database; record its new url.
        name = 'test2'
        response = self.session.post(self.db_url, json={'name': name})
        self.assertEqual(response.status_code, http.client.OK)
        result = response.json()
        json_validate(result, dbshare.schema.db.output)
        self.assertTrue(result['$id'].endswith(name))

        # So that the database is deleted at cleanup.
        self.db_url = result['$id']
        self.addCleanup(self.delete_db)

    def test_readonly(self):
        "Create an empty database, set to read-only, then read-write."

        # Create empty database.
        response = self.create_database()
        self.assertEqual(response.status_code, http.client.OK)

        # Set to read-only.
        response = self.session.post(f"{self.db_url}/readonly")
        self.assertEqual(response.status_code, http.client.OK)
        result = response.json()
        json_validate(result, dbshare.schema.db.output)
        self.assertTrue(result['readonly'])
        self.assertTrue(len(result['hashes']))

        # Try editing the database; should fail.
        title = 'New title'
        response = self.session.post(self.db_url, json={'title': title})
        self.assertEqual(response.status_code, http.client.UNAUTHORIZED)

        # Set to read-write.
        response = self.session.post(f"{self.db_url}/readwrite")
        self.assertEqual(response.status_code, http.client.OK)
        result = response.json()
        json_validate(result, dbshare.schema.db.output)
        self.assertFalse(result['readonly'])
        self.assertFalse(len(result['hashes']))

        # Delete the database.
        response = self.session.delete(self.db_url)
        self.assertEqual(response.status_code, http.client.NO_CONTENT)


if __name__ == '__main__':
    run()
