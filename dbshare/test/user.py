"Test the user API endpoint."

import http.client
import os

import base


class User(base.Base):
    "Test the user API endpoint."

    def test_access(self):
        "Get JSON for the current user."
        response = self.session.get(base.url('user', base.CONFIG['username']))
        self.assertEqual(response.status_code, http.client.OK)

    def test_schema(self):
        "Valid user JSON."
        response = self.session.get(base.url('user', base.CONFIG['username']))
        self.assertEqual(response.status_code, http.client.OK)
        schema = self.get_schema(response)
        self.assertTrue(schema is not None)
        base.json_validate(response.json(), schema)


if __name__ == '__main__':
    run()
