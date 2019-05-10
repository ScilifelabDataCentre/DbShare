"Test the top-level DbPortal API."

import json
import unittest

import requests

with open('config.json') as infile:
    CONFIG = json.load(infile)


class AppTest(unittest.TestCase):
    "Test the top-level DbPortal API."

    def testAccess(self):
        "Access to the API root."
        response = requests.get(CONFIG['root'])
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue('title' in data)
        self.assertTrue('databases' in data)
        self.assertTrue('templates' in data)

if __name__ == '__main__':
    unittest.main()
