"Test the root API endpoint."

import http.client

from dbshare.test.base import *

import dbshare.schema.root


class Root(Base):
    "Test the root API endpoint."

    def test_access(self):
        "Access to the root API."
        response = self.session.get(URL())
        self.assertEqual(response.status_code, http.client.OK)

    def test_redirect(self):
        "Redirect to the root API from HTML home page if Accept header set."
        response = self.session.get(CONFIG['base_url'],
                                    headers={'Accept': 'application/json'})
        self.assertEqual(response.status_code, http.client.OK)
        self.assertEqual(response.url, CONFIG['root_url'])

    def test_schema(self):
        "Valid root API JSON."
        response = self.session.get(URL())
        self.assertEqual(response.status_code, http.client.OK)
        json_validate(response.json(), dbshare.schema.root.schema)


if __name__ == '__main__':
    run()
