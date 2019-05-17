"Test the user API endpoint."

import http.client
import os

import dbshare.schema.user

from dbshare.test.base import *


class User(Base):
    "Test the user API endpoint."

    def setUp(self):
        super().setUp()
        self.user_url = f"{CONFIG['root_url']}/user/{CONFIG['username']}"

    def test_schema(self):
        "Schema for user API JSON."
        response = self.session.get(self.user_url)
        self.assertEqual(response.status_code, http.client.OK)
        jsonschema.validate(instance=response.json(),
                            schema=dbshare.schema.user.schema)


if __name__ == '__main__':
    unittest.main()
