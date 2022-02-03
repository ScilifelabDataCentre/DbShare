"Test the users API endpoint."

import http.client

import base


class Users(base.Base):
    "Test the user API endpoint."

    def test_access(self):
        "Get JSON for the user list."
        response = self.session.get(self.root['users']['all']['href'])
        self.assertEqual(response.status_code, http.client.OK)

    def test_schema(self):
        "Valid user list JSON."
        response = self.session.get(self.root['users']['all']['href'])
        self.check_schema(response)


if __name__ == '__main__':
    base.run()
