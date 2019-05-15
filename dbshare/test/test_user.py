"Test the DbShare API user endpoint."

import http.client
import os

import dbshare.schema.user

from dbshare.test.base import *


class User(Base):
    "Test the DbShare API user endpoint."

    def test_schema(self):
        "Test schema for user JSON."
        url = f"{CONFIG['root']}/user/profile/{CONFIG['username']}"
        response = self.session.get(url)
        self.assertEqual(response.status_code, http.client.OK)
        jsonschema.validate(instance=response.json(),
                            schema=dbshare.schema.user.schema)


if __name__ == '__main__':
    unittest.main()
