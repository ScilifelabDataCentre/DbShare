"Test the DbShare API dbs endpoint."

import http.client

from dbshare.test.base import *

import dbshare.schema.dbs


class Dbs(Base):
    "Test the DbShare API dbs endpoint."

    def setUp(self):
        super().setUp()
        response = self.session.get(CONFIG['root_url'])
        self.assertEqual(response.status_code, http.client.OK)
        data = response.json()
        self.dbs_urls = {}
        for key in ['public', 'owner', 'all']:
            self.dbs_urls[key] = data['databases'][key]['href']

    def test_schema(self):
        "Test validity of the API dbs JSON."
        for key in ['public', 'owner', 'all']:
            response = self.session.get(self.dbs_urls[key])
            self.assertEqual(response.status_code, http.client.OK)
            jsonschema.validate(instance=response.json(),
                                schema=dbshare.schema.dbs.schema)


if __name__ == '__main__':
    unittest.main()
