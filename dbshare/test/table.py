"Test the table API endpoint."

import http.client

import dbshare.schema.db
import dbshare.schema.table
import dbshare.schema.rows

from dbshare import constants
from dbshare.test.base import *


class Table(Base):
    "Test the DbShare API table endpoint."

    def test_db_upload(self):
        "Create a database with table by file upload, check the table JSON."

        # Upload a file containing a plain Sqlite3 database.
        response = self.upload_file()
        self.assertEqual(response.status_code, http.client.OK)

        # The db API JSON is valid.
        jsonschema.validate(instance=response.json(),
                            schema=dbshare.schema.db.schema)

        # The table API JSON is valid.
        table_url = f"{CONFIG['root_url']}/table/{CONFIG['dbname']}/t1"
        response = self.session.get(table_url)
        self.assertEqual(response.status_code, http.client.OK)
        jsonschema.validate(instance=response.json(),
                            schema=dbshare.schema.table.schema)

        # The table rows JSON is valid.
        rows_url = f"{CONFIG['base_url']}/table/{CONFIG['dbname']}/t1.json"
        response = self.session.get(rows_url)
        self.assertEqual(response.status_code, http.client.OK)
        jsonschema.validate(instance=response.json(),
                            schema=dbshare.schema.rows.schema)

        # Content negotiation for rows. No '.json' extension.
        rows_url = f"{CONFIG['base_url']}/table/{CONFIG['dbname']}/t1"
        response = self.session.get(rows_url,
                                    headers={'Accept': constants.JSON_MIMETYPE})
        self.assertEqual(response.status_code, http.client.OK)
        jsonschema.validate(instance=response.json(),
                            schema=dbshare.schema.rows.schema)


if __name__ == '__main__':
    unittest.main()
