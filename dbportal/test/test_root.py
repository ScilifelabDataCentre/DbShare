"Test the DbPortal API root endpoint."

from dbportal.test.base import *

import dbportal.schema.root


class Root(Base):
    "Test the DbPortal API dbs endpoint."

    def test_access(self):
        "Test access to the API root."
        response = self.session.get(CONFIG['root'])
        self.assertEqual(response.status_code, 200)

    def test_redirect(self):
        "Test redirect to the API root from HTML home page."
        url = CONFIG['root'].strip('/api')
        response = self.session.get(url, headers={'Accept': 'application/json'})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.url, CONFIG['root'])

    def test_schema(self):
        "Test validity of the API root JSON."
        response = self.session.get(CONFIG['root'])
        self.assertEqual(response.status_code, 200)
        jsonschema.validate(instance=response.json(),
                            schema=dbportal.schema.root.schema)


if __name__ == '__main__':
    unittest.main()
