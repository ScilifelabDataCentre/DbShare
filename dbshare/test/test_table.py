"Test the DbShare API table endpoint."

import http.client
import sqlite3

import dbshare.schema.db
import dbshare.schema.table

from dbshare.test.base import *


class Table(Base):
    "Test the DbShare API table endpoint."

    def setUp(self):
        super().setUp()
        self.db_url = f"{CONFIG['root_url']}/db/{CONFIG['dbname']}"
        self.addCleanup(self.delete_db)

    def delete_db(self):
        self.session.delete(self.db_url)

    def test_db_upload(self):
        "Create a database with table by file upload, check the table JSON."
        # Create the database in a local file.
        cnx = sqlite3.connect(CONFIG['filename'])
        self.addCleanup(self.delete_file)
        # Create a table in the database.
        cnx.execute(f"CREATE TABLE {CONFIG['tablename']} ("
                    "i INTEGER PRIMARY KEY,"
                    "r REAL,"
                    "t TEXT NOT NULL)")
        cnx.execute(f"INSERT INTO {CONFIG['tablename']} (i,r,t)"
                    " VALUES (?,?,?)", (1, 2.1, 'a'))
        cnx.execute(f"INSERT INTO {CONFIG['tablename']} (i,r,t)"
                    " VALUES (?,?,?)", (2, 0.5, 'b'))
        cnx.close()
        # Upload the database file.
        with open(CONFIG['filename'], 'rb') as infile:
            response = self.session.put(self.db_url, data=infile)
        self.assertEqual(response.status_code, http.client.OK)
        # Check that API db JSON is valid.
        jsonschema.validate(instance=response.json(),
                            schema=dbshare.schema.db.schema)
        # Check that API table JSON is valid.
        table_url = f"{CONFIG['root_url']}/table/{CONFIG['dbname']}/{CONFIG['tablename']}"
        response = self.session.get(table_url)
        self.assertEqual(response.status_code, http.client.OK)
        jsonschema.validate(instance=response.json(),
                            schema=dbshare.schema.table.schema)
        # Check that API rows JSON is valid.
        rows_url = f"{CONFIG['base_url']}/table/{CONFIG['dbname']}/{CONFIG['tablename']}.json"
        response = self.session.get(rows_url)
        self.assertEqual(response.status_code, http.client.OK)
        jsonschema.validate(instance=response.json(),
                            schema=dbshare.schema.table.rows_schema)


if __name__ == '__main__':
    unittest.main()
