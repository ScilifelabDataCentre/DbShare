"Test the DbShare API root endpoint."

import http.client

from dbshare.test.base import *

import dbshare.schema.root


class Root(Base):
    "Test the DbShare API dbs endpoint."

    def test_access(self):
        "Test access to the API root."
        response = self.session.get(CONFIG['root'])
        self.assertEqual(response.status_code, http.client.OK)

    def test_redirect(self):
        "Test redirect to the API root from HTML home page."
        url = CONFIG['root'].strip('/api')
        response = self.session.get(url, headers={'Accept': 'application/json'})
        self.assertEqual(response.status_code, http.client.OK)
        self.assertEqual(response.url, CONFIG['root'])

    def test_schema(self):
        "Test validity of the API root JSON."
        response = self.session.get(CONFIG['root'])
        self.assertEqual(response.status_code, http.client.OK)
        jsonschema.validate(instance=response.json(),
                            schema=dbshare.schema.root.schema)


if __name__ == '__main__':
    unittest.main()
