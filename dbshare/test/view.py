"Test the view API endpoint."

import http.client
import json

import base


class View(base.Base):
    "Test the view API endpoint."

    def test_db_upload(self):
        "Create a database with view by file upload, check the view JSON."
        response = self.upload_file()
        result = self.check_schema(response)
        url = result['views'][0]['href']
        response = self.session.get(url)
        result = self.check_schema(response)
        url = result['rows']['href']
        response = self.session.get(url)
        result = self.check_schema(response)
        self.assertEqual(result['nrows'], 2)
        self.assertEqual(len(result['data']), 2)

    def test_name_clash(self):
        "Try creating a view with uppercase name of already existing."
        response = self.upload_file()
        result = self.check_schema(response)
        view_spec = {
            'name': 'V1',
            'query': {'from': 't1',
                      'select': 'r',
                      'where': 'i>=3'}
        }
        url = self.root['operations']['view']['create']['href']
        url = url.format(dbname=base.CONFIG['dbname'],
                         viewname=view_spec['name'])
        response = self.session.put(url, json=view_spec)
        self.assertEqual(response.status_code, http.client.BAD_REQUEST)

    def test_create_delete(self):
        "Create a new view, test it, delete it."
        response = self.upload_file()
        result = self.check_schema(response)
        view_spec = {
            'name': 'v2',
            'query': {'from': 't1',
                      'select': 'r',
                      'where': 'i>=3'}
        }
        url = self.root['operations']['view']['create']['href']
        url = url.format(dbname=base.CONFIG['dbname'],
                         viewname=view_spec['name'])
        response = self.session.put(url, json=view_spec)
        result = self.check_schema(response)

        # Test the content of the view.
        url = result['rows']['href']
        response = self.session.get(url)
        result = self.check_schema(response)
        self.assertEqual(result['nrows'], 1)
        self.assertEqual(result['data'][0]['r'], -1.5)

        # Delete the view.
        url = self.root['operations']['view']['delete']['href']
        url = url.format(dbname=base.CONFIG['dbname'],
                         viewname=view_spec['name'])
        response = self.session.delete(url)
        self.assertEqual(response.status_code, http.client.NO_CONTENT)


if __name__ == '__main__':
    base.run()
