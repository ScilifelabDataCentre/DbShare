"Test the user API endpoint."

import http.client
import os

import dbshare.schema.user

from dbshare.test.base import *


class User(Base):
    "Test the user API endpoint."

    def test_schema(self):
        "Valid user JSON."
        response = self.session.get(URL('user', CONFIG['username']))
        self.assertEqual(response.status_code, http.client.OK)
        json_validate(response.json(), dbshare.schema.user.schema)


if __name__ == '__main__':
    run()
