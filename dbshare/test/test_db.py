"Test the DbShare API db endpoint."

import http.client
import os
import sqlite3

from dbshare.test.base import *


class Db(Base):
    "Test the DbShare API db endpoint."

    def test_create_scratch(self):
        "Test creation of a database from scratch, and its deletion."
        dbname = 'test'
        url = f"{CONFIG['root']}/db/{dbname}"
        response = self.session.put(url)
        self.assertEqual(response.status_code, http.client.OK)
        response = self.session.delete(url)
        self.assertEqual(response.status_code, http.client.NO_CONTENT)

    def test_create_file(self):
        "Test creation of a database from file content, and its deletion."
        filename = '/tmp/test.sqlite3'
        try:
            os.remove(filename)
        except OSError:
            pass
        cnx = sqlite3.connect(filename)
        cnx.execute("CREATE TABLE t1 (i INT PRIMARY KEY)")
        cnx.execute("INSERT INTO t1 (i) VALUES (?)", (1,))
        cnx.execute("INSERT INTO t1 (i) VALUES (?)", (2,))
        cnx.close()
        dbname = 'test'
        url = f"{CONFIG['root']}/db/{dbname}"
        with open(filename, 'rb') as infile:
            response = self.session.put(url, data=infile)
        self.assertEqual(response.status_code, http.client.OK)
        response = self.session.delete(url)
        self.assertEqual(response.status_code, http.client.NO_CONTENT)
        os.remove(filename)


if __name__ == '__main__':
    unittest.main()
