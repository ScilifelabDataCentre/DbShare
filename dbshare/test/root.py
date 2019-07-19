"Test the root API endpoint."

import http.client
import logging

import base

class Root(base.Base):
    "Test the root API endpoint."

    def test_access(self):
        "Access to the root API."
        response = self.session.get(base.CONFIG['root_url'])
        self.assertEqual(response.status_code, http.client.OK)

    def test_redirect(self):
        "Redirect to the root API from HTML home page if Accept header set."
        response = self.session.get(base.CONFIG['root_url'],
                                    headers={'Accept': 'application/json'})
        self.assertEqual(response.status_code, http.client.OK)
        self.assertEqual(response.url, base.CONFIG['root_url'])

    def test_schema(self):
        "Get the schema and check valid root API JSON."
        response = self.session.get(base.CONFIG['root_url'])
        self.check_schema(response)


if __name__ == '__main__':
    base.run()
