# Tutorial: Using the API

The API can be used to access and edit databases and their data.

A user account is needed (except for reading public data) and the
authentication is based on an API key set for the user account.

- Go to your [user account page](/user/profile).
- If your API is has not been set, click **Edit**.
- Check the box **API key** and do **Save**.

In this tutorial, the third-party package
[**`requests`**](https://requests.kennethreitz.org/en/master/) is used.

### Example Python script with comments

    import json
    import requests

    URL = 'https://dbshare.scilifelab.se/api'    # Replace with your site.
    APIKEY = '4e7a...'                           # Replace with your value.

    response = requests.get(URL, headers={'x-apikey': APIKEY})
    print(response.status_code)                  # 200
    print(json.dumps(response.json(), indent=2)) # Indent for nicer output

    # The JSON for the API root contains information of the full set of
    # operations available in the form of template URLs with descriptions of
    # the variables and methods.


    # Create a database called 'newdb'

    url = URL + '/db/newdb'
    response = requests.put(url, headers={'x-apikey': APIKEY})
    print(response.status_code)                  # 200
    print(json.dumps(response.json(), indent=2)) # Show db information


    # Create a table called 't1' in the 'newdb' database

    SCHEMA = {
      'name': 't1',
      'columns': [{'name': 'i', 'type': 'INTEGER', 'primarykey': True},
                  {'name': 't', 'type': 'TEXT', 'notnull': False}]
    }

    url = URL + '/table/newdb/t1'
    response = requests.put(url, headers={'x-apikey': APIKEY}, json=SCHEMA)
    print(response.status_code)                  # 200
    print(json.dumps(response.json(), indent=2)) # Show table information


    # Insert data; add two rows to the table

    DATA = {'data': [{'i': 1, 't': 'Some text'},
                     {'i': 2, 't': 'More text'}]
    }

    url = URL + '/table/newdb/t1/insert'
    response = requests.post(url, headers={'x-apikey': APIKEY}, json=DATA)
    print(response.status_code)                  # 200
    result = response.json()
    print(json.dumps(result, indent=2))          # Show table information

    url = result['rows']['href']                 # Url for the JSON rows data
                                                 # NOTE: does not contain 'api'!
    response = requests.get(url,  headers={'x-apikey': APIKEY})
    print(response.status_code)                  # 200
    print(json.dumps(result, indent=2))          # Show table rows data


    # Try invalid data: primary key already used

    DATA = {'data': [{'i': 1, 't': 'Wrong record'}]}
    url = URL + '/table/newdb/t1/insert'
    response = requests.post(url, headers={'x-apikey': APIKEY}, json=DATA)
    print(response.status_code)                  # 400 !
    result = response.json()
    print(json.dumps(result, indent=2))          # Show error information
