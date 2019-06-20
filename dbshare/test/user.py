"Test the user API endpoint."

import http.client
import os

import base


class User(base.Base):
    "Test the user API endpoint."

    def test_access(self):
        "Get JSON for the current user."
        response = self.session.get(self.root['user']['href'])
        self.assertEqual(response.status_code, http.client.OK)

    def test_schema(self):
        "Valid user JSON."
        response = self.session.get(self.root['user']['href'])
        self.check_schema(response)


if __name__ == '__main__':
    base.run()
