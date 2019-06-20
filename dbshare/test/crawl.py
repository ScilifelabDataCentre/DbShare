"Crawl all hrefs from the API root down."

import http.client
import re
import urllib.parse

import base

PATH_RX = re.compile(r"^/api/(db|table|view)/([^/]+)")


class Crawl(base.Base):
    "Crawl all hrefs from the API root down."

    def setUp(self):
        "Upload a file containing a plain Sqlite3 database."
        super().setUp()
        self.upload_file()
        self.remaining = set()
        self.checked = set()
        self.failed = set()

    def test_crawl(self):
        "Start at the root and find all hrefs from there."
        response = self.session.get(base.CONFIG['root_url'])
        self.assertEqual(response.status_code, http.client.OK)
        self.extract(response.json())
        while self.remaining:
            url = self.remaining.pop()
            response = self.session.get(url)
            self.checked.add(url)
            if response.status_code != http.client.OK:
                self.failed.add(url)
            elif response.headers.get('content-type') == 'application/json':
                try:
                    self.extract(response.json())
                except ValueError:
                    self.failed.add(url)
        self.assertFalse(self.failed, '\n'.join(list(self.failed)))

    def extract(self, data):
        "Find all hrefs in the data."
        if isinstance(data, dict):
            # Skip if it is a URI template.
            if 'variables' in data: return
            # Skip if it is a non-GET method
            if data.get('method', 'GET') != 'GET': return
            for key, value in data.items():
                if key == 'href':
                    if value in self.checked: continue
                    if not value.startswith(base.CONFIG['root_url']): continue
                    parts = urllib.parse.urlparse(value)
                    match = PATH_RX.match(parts.path)
                    if match and match.group(2) != base.CONFIG['dbname']:
                        continue
                    self.remaining.add(value)
                else:
                    self.extract(value)
        elif isinstance(data, list):
            for value in data:
                self.extract(value)


if __name__ == '__main__':
    base.run()
