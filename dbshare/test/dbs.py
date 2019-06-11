"Test the dbs API endpoint."

import http.client

from dbshare.test.base import *

import dbshare.schema.dbs


class Dbs(Base):
    "Test the dbs API endpoint."

    def test_schema(self):
        "Valid databases map JSON."

        # Get the URLs for the different lists of databases.
        response = self.session.get(URL())
        self.assertEqual(response.status_code, http.client.OK)
        data = response.json()
        dbs_urls = {}
        for key in ['public', 'owner', 'all']:
            dbs_urls[key] = data['databases'][key]['href']

        # Valid JSON for dbs lists.
        for key in ['public', 'owner', 'all']:
            response = self.session.get(dbs_urls[key])
            self.assertEqual(response.status_code, http.client.OK)
            json_validate(response.json(), dbshare.schema.dbs.schema)


if __name__ == '__main__':
    run()
