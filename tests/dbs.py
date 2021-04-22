"Test the dbs API endpoint."

import http.client

import base


class Dbs(base.Base):
    "Test the dbs API endpoint."

    def test_access(self):
        "Are all database collection links available?"
        for key in ['public', 'owner', 'all']:
            self.assertTrue(key in self.root['databases'])

    def test_schema(self):
        "Valid databases map JSON."

        # Get the URLs for the different lists of databases.
        dbs_urls = {}
        for key in ['public', 'owner', 'all']:
            dbs_urls[key] = self.root['databases'][key]['href']

        # Valid JSON for dbs lists.
        for key in ['public', 'owner', 'all']:
            response = self.session.get(dbs_urls[key])
            self.check_schema(response)


if __name__ == '__main__':
    base.run()
