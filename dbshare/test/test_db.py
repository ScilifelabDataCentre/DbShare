"Test the DbShare API db endpoint."

import http.client
import sqlite3

import dbshare.schema.db

from dbshare.test.base import *


class Db(Base):
    "Test the DbShare API db endpoint."

    def setUp(self):
        super().setUp()
        self.db_url = f"{CONFIG['root_url']}/db/{CONFIG['dbname']}"

    def delete_db(self):
        self.session.delete(self.db_url)

    def test_create_scratch(self):
        "Create an empty database from scratch, check it JSON, and delete it."
        response = self.session.put(self.db_url)
        self.assertEqual(response.status_code, http.client.OK)
        jsonschema.validate(instance=response.json(),
                            schema=dbshare.schema.db.schema)
        response = self.session.delete(self.db_url)
        self.assertEqual(response.status_code, http.client.NO_CONTENT)

    def test_create_upload(self):
        "Create a database by file upload, check its JSON, and delete it."
        cnx = sqlite3.connect(CONFIG['filename'])
        self.addCleanup(self.delete_file)
        cnx.execute(f"CREATE TABLE {CONFIG['tablename']} (i INTEGER PRIMARY KEY)")
        cnx.execute(f"INSERT INTO {CONFIG['tablename']} (i) VALUES (?)", (1,))
        cnx.execute(f"INSERT INTO {CONFIG['tablename']} (i) VALUES (?)", (2,))
        cnx.close()
        with open(CONFIG['filename'], 'rb') as infile:
            response = self.session.put(self.db_url, data=infile)
        self.addCleanup(self.delete_db)
        self.assertEqual(response.status_code, http.client.OK)
        jsonschema.validate(instance=response.json(),
                            schema=dbshare.schema.db.schema)
        response = self.session.delete(self.db_url)
        self.assertEqual(response.status_code, http.client.NO_CONTENT)


if __name__ == '__main__':
    unittest.main()
