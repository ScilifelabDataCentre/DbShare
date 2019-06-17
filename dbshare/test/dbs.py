"Test the dbs API endpoint."

import http.client

import base


class Dbs(base.Base):
    "Test the dbs API endpoint."

    def test_access(self):
        "Are all database collection links available?"
        response = self.session.get(base.url())
        self.assertEqual(response.status_code, http.client.OK)
        data = response.json()
        for key in ['public', 'owner', 'all']:
            self.assertTrue(key in data['databases'])

    def test_schema(self):
        "Valid databases map JSON."

        # Get the URLs for the different lists of databases.
        response = self.session.get(base.url())
        self.assertEqual(response.status_code, http.client.OK)
        data = response.json()
        dbs_urls = {}
        for key in ['public', 'owner', 'all']:
            dbs_urls[key] = data['databases'][key]['href']

        # Valid JSON for dbs lists.
        for key in ['public', 'owner', 'all']:
            response = self.session.get(dbs_urls[key])
            self.assertEqual(response.status_code, http.client.OK)
            schema = self.get_schema(response)
            self.assertTrue(schema is not None)
            base.json_validate(response.json(), schema)


if __name__ == '__main__':
    base.run()
