"Test the DbPortal API dbs endpoint."

from dbportal.test.base import *

import dbportal.schema.dbs


class Dbs(Base):
    "Test the DbPortal API dbs endpoint."

    def setUp(self):
        super().setUp()
        response = self.session.get(CONFIG['root'])
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.dbs_urls = {}
        for key in ['public', 'owner', 'all']:
            self.dbs_urls[key] = data['databases'][key]['href']

    def test_schema(self):
        "Test validity of the API dbs JSON."
        for key in ['public', 'owner', 'all']:
            response = self.session.get(self.dbs_urls[key])
            self.assertEqual(response.status_code, 200)
            jsonschema.validate(instance=response.json(),
                                schema=dbportal.schema.dbs.schema)


if __name__ == '__main__':
    unittest.main()
