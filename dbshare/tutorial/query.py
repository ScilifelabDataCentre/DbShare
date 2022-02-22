"Script showing use of the query API use."

import requests
import pprint

url = "https://dbshare.scilifelab.se/api/query/demo"

query = {"select": "*", "from": "iris_flower_measurements", "limit": 10}

response = requests.get(url, json=query)
print(response.status_code)
pprint.pprint(response.json())
