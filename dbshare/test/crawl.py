"Crawl all hrefs from the API root down."

import http.client

import base

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
        print(base.CONFIG['root_url'])
        response = self.session.get(base.CONFIG['root_url'])
        self.assertEqual(response.status_code, http.client.OK)
        self.extract(response.json())
        while self.remaining:
            url = self.remaining.pop()
            # XXX skip tables and views not in 'test' database
            print(url)
            response = self.session.get(url)
            self.checked.add(url)
            if response.status_code != http.client.OK:
                self.failed.add(url)
            elif url.startswith(base.CONFIG['base_url']):
                if response.headers.get('content-type') == 'application/json':
                    try:
                        self.extract(response.json())
                    except ValueError:
                        self.failed.add(url)
        self.assertFalse(self.failed, '\n'.join(list(self.failed)))

    def extract(self, data):
        "Find all hrefs in the data."
        if isinstance(data, dict):
            for key, value in data.items():
                if key == 'href':
                    if value not in self.checked:
                        self.remaining.add(value)
                else:
                    self.extract(value)
        elif isinstance(data, list):
            for value in data:
                self.extract(value)


if __name__ == '__main__':
    base.run()
