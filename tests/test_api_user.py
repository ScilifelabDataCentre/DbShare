"""Test API ordinary user access.

Uses the 'requests' package.
"""

import csv
import http.client
import io

import requests
import pytest

import dbshare
import utils


@pytest.fixture(scope="module")
def settings():
    "Get the settings from file 'settings.json' in this directory."
    result = utils.get_settings(
        BASE_URL="http://localhost:5001", USER_USERNAME=None, USER_APIKEY=None
    )
    # Set up requests session with API key.
    result["session"] = session = requests.Session()
    session.headers.update({"x-apikey": result["USER_APIKEY"]})
    # Get the schema.
    response = session.get(f"{result['BASE_URL']}/api/schema/root")
    assert response.status_code == http.client.OK
    result["root_schema"] = response.json()
    response = session.get(f"{result['BASE_URL']}/api/schema/dbs")
    assert response.status_code == http.client.OK
    result["dbs_schema"] = response.json()
    response = session.get(f"{result['BASE_URL']}/api/schema/db")
    assert response.status_code == http.client.OK
    result["db_schema"] = response.json()
    response = session.get(f"{result['BASE_URL']}/api/schema/table")
    assert response.status_code == http.client.OK
    result["table_schema"] = response.json()
    response = session.get(f"{result['BASE_URL']}/api/schema/rows")
    assert response.status_code == http.client.OK
    result["rows_schema"] = response.json()
    response = session.get(f"{result['BASE_URL']}/api/schema/view")
    assert response.status_code == http.client.OK
    result["view_schema"] = response.json()
    response = session.get(f"{result['BASE_URL']}/api/schema/view/create")
    assert response.status_code == http.client.OK
    result["view_create_schema"] = response.json()

    yield result

    result["session"].close()


@pytest.fixture()
def database(settings):
    "Upload the test database, and delete it."
    session = settings["session"]

    # Upload the database.
    settings["url"] = url = f"{settings['BASE_URL']}/api/db/test"
    with open("test.sqlite3", "rb") as infile:
        headers = {"Content-Type": "application/x-sqlite3"}
        response = session.put(url, data=infile, headers=headers)
        assert response.status_code == http.client.OK
    data = response.json()
    assert len(data["tables"]) == 1
    assert len(data["views"]) == 0
    table = data["tables"][0]
    assert table["name"] == "t1"
    assert table["nrows"] == 3

    yield

    # Delete the database.
    response = session.delete(url)


def test_root(settings):
    "Test the root and some links from it."
    session = settings["session"]

    response = session.get(f"{settings['BASE_URL']}/api")
    assert response.status_code == http.client.OK
    data = response.json()
    utils.validate_schema(data, settings["root_schema"])
    assert data["version"] == dbshare.__version__
    # Loop over schema.
    for href in utils.get_hrefs(data["schema"]):
        response = session.get(href)
        assert response.status_code == http.client.OK


def test_databases(settings):
    "Test access to the databases."
    session = settings["session"]

    # Check the sets of databases.
    response = session.get(f"{settings['BASE_URL']}/api")
    assert response.status_code == http.client.OK
    data = response.json()
    assert set(data["databases"]) == {"public", "owner"}
    for category in data["databases"]:
        href = data["databases"][category]["href"]
        response = session.get(href)
        assert response.status_code == http.client.OK
        utils.validate_schema(response.json(), settings["dbs_schema"])


def test_create_database(settings):
    "Test creating and deleting a database."
    session = settings["session"]

    # Create the database.
    url = f"{settings['BASE_URL']}/api/db/test"
    response = session.put(url)
    assert response.status_code == http.client.OK
    data = response.json()
    assert len(data["tables"]) == 0
    assert len(data["views"]) == 0

    # Delete the test database.
    session.delete(url)


def test_upload_database(settings, database):
    "Test uploading a database Sqlite3 file."
    session = settings["session"]
    url = f"{settings['BASE_URL']}/api/db/bad"

    # Attempt bad upload.
    headers = {"Content-Type": "application/garbage"}
    response = session.put(url, data="garbage", headers=headers)
    assert response.status_code == http.client.UNSUPPORTED_MEDIA_TYPE


def test_table(settings, database):
    "Test creating, modifying and deleting a table."
    session = settings["session"]
    url = settings["url"]

    # Create a table.
    table_spec = {
        "name": "t2",
        "title": "Test table",
        "columns": [
            {"name": "i", "type": "INTEGER", "primarykey": True},
            {"name": "t", "type": "TEXT", "notnull": False},
            {"name": "r", "type": "REAL", "notnull": True},
        ],
    }
    table_url = f"{settings['BASE_URL']}/api/table/test/t2"
    response = session.put(table_url, json=table_spec)
    assert response.status_code == http.client.OK
    data = response.json()
    utils.validate_schema(data, settings["table_schema"])

    # Check the created table.
    assert len(data["columns"]) == len(table_spec["columns"])
    assert data["title"] == table_spec["title"]
    lookup = dict([(c["name"], c) for c in table_spec["columns"]])
    for column in data["columns"]:
        assert column["name"] in lookup
        assert column["type"] == lookup[column["name"]]["type"]

    # PRIMAY KEY implies NOT NULL.
    lookup = dict([(c["name"], c) for c in data["columns"]])
    assert lookup["i"]["primarykey"]
    assert lookup["i"]["notnull"]

    # Insert rows into the table.
    url = f"{settings['BASE_URL']}/api/table/test/t2/insert"
    row = {"data": [{"i": 1, "t": "stuff", "r": 1.2345}]}
    response = session.post(url, json=row)
    data = response.json()
    utils.validate_schema(data, settings["table_schema"])
    assert data["nrows"] == 1

    row = {"data": [{"i": 2, "t": "another", "r": 3}]}
    response = session.post(url, json=row)
    assert response.status_code == http.client.OK
    data = response.json()
    utils.validate_schema(data, settings["table_schema"])
    assert data["nrows"] == 2

    row = {"data": [{"i": 3, "r": -0.45}]}
    response = session.post(url, json=row)
    assert response.status_code == http.client.OK
    data = response.json()
    utils.validate_schema(data, settings["table_schema"])
    assert data["nrows"] == 3

    row_3 = {"i": 4, "t": "multirow", "r": -0.45}
    rows = {"data": [row_3, {"i": 5, "t": "multirow 2", "r": 1.2e4}]}
    response = session.post(url, json=rows)
    assert response.status_code == http.client.OK
    data = response.json()
    utils.validate_schema(data, settings["table_schema"])
    assert data["nrows"] == 5

    # Try to insert invalid data of different kinds.
    row = {"data": [{"i": 3, "t": "primary key clash", "r": -0.1}]}
    response = session.post(url, json=row)
    assert response.status_code == http.client.BAD_REQUEST

    row = {"data": [{"i": 8, "t": "missing value"}]}
    response = session.post(url, json=row)
    assert response.status_code == http.client.BAD_REQUEST

    row = {"data": [{"i": 9, "t": "wrong type", "r": "string!"}]}
    response = session.post(url, json=row)
    assert response.status_code == http.client.BAD_REQUEST

    # Get the table data.
    response = session.get(table_url)
    assert response.status_code == http.client.OK
    data = response.json()
    utils.validate_schema(data, settings["table_schema"])
    assert data["nrows"] == 5

    # Get the rows and compare one of them.
    url = data["rows"]["href"]
    response = session.get(url)
    data = response.json()
    utils.validate_schema(data, settings["rows_schema"])
    assert data["nrows"] == 5
    assert len(data["data"]) == data["nrows"]
    assert data["data"][3] == row_3

    # Empty the table.
    url = f"{settings['BASE_URL']}/api/table/test/t2/empty"
    response = session.post(url)
    assert response.status_code == http.client.OK
    response = session.get(response.url)
    data = response.json()
    assert data["nrows"] == 0


def test_csv(settings, database):
    "Test CSV operations on a table."
    session = settings["session"]

    # Create the table.
    table_spec = {
        "name": "t2",
        "title": "Test table",
        "columns": [
            {"name": "i", "type": "INTEGER", "primarykey": True},
            {"name": "t", "type": "TEXT", "notnull": False},
            {"name": "r", "type": "REAL", "notnull": True},
        ],
    }
    table_url = f"{settings['BASE_URL']}/api/table/test/t2"
    response = session.put(table_url, json=table_spec)
    assert response.status_code == http.client.OK
    data = response.json()
    utils.validate_schema(data, settings["table_schema"])

    rows = [
        {"i": 1, "t": "some text", "r": 1.43},
        {"i": 2, "t": "Blah", "r": 0.43},
        {"i": 3, "t": "blopp", "r": 109.1},
        {"i": 4, "t": "more", "r": -0.213},
    ]
    textfile = io.StringIO()
    writer = csv.DictWriter(textfile, list(rows[0].keys()))
    writer.writeheader()
    writer.writerows(rows)
    headers = {'Content-Type': 'text/csv'}
    response = session.post(f"{table_url}/insert", data=textfile.getvalue(), headers=headers)
    assert response.status_code == http.client.OK
    data = response.json()
    utils.validate_schema(data, settings["table_schema"])
    assert data["nrows"] == len(rows)

    # Try inserting a bad row: no primary key.
    rows = [
        {"t": "missing primary key", "r": 1.43},
    ]
    textfile = io.StringIO()
    writer = csv.DictWriter(textfile, list(rows[0].keys()))
    writer.writeheader()
    writer.writerows(rows)
    response = session.post(f"{table_url}/insert", data=textfile.getvalue(), headers=headers)
    assert response.status_code == http.client.BAD_REQUEST

    # Try inserting a bad row: missing NOT NULL item.
    rows = [
        {"i": 5, "t": "missing primary key"},
    ]
    textfile = io.StringIO()
    writer = csv.DictWriter(textfile, list(rows[0].keys()))
    writer.writeheader()
    writer.writerows(rows)
    response = session.post(f"{table_url}/insert", data=textfile.getvalue(), headers=headers)
    assert response.status_code == http.client.BAD_REQUEST

    # Insert more data.
    rows = [
        {"i": 5, "t": "yet more text", "r": 1.0e5},
        {"i": 6, "t": "a name", "r": -0.001},
    ]
    textfile = io.StringIO()
    writer = csv.DictWriter(textfile, list(rows[0].keys()))
    writer.writeheader()
    writer.writerows(rows)
    response = session.post(f"{table_url}/insert", data=textfile.getvalue(), headers=headers)
    assert response.status_code == http.client.OK
    data = response.json()
    utils.validate_schema(data, settings["table_schema"])
    assert data["nrows"] == 6

    # def test_update(self):
    #     "Create database and table; insert and update using CSV."

    #     # Create an empty database.
    #     response = self.create_database()
    #     self.assertEqual(response.status_code, http.client.OK)
    #     result = self.check_schema(response)

    #     # Create a table in the database.
    #     url = self.root['operations']['table']['create']['href']
    #     url = url.format(dbname=base.SETTINGS['dbname'],
    #                      tablename=self.table_spec['name'])
    #     response = self.session.put(url, json=self.table_spec)
    #     result = self.check_schema(response)
    #     self.assertEqual(result['nrows'], 0)

    #     # Insert CSV data.
    #     headers = {'Content-Type': 'text/csv'}
    #     url = self.root['operations']['table']['insert']['href']
    #     url = url.format(dbname=base.SETTINGS['dbname'],
    #                      tablename=self.table_spec['name'])
    #     data = self.get_csvfile_data([(1, 'test', 0.2),
    #                                   (2, 'another test', 4.123e5),
    #                                   (3, 'third', -13)])
    #     response = self.session.post(url, data=data, headers=headers)
    #     result = self.check_schema(response)
    #     self.assertEqual(result['nrows'], 3)

    #     # Update CSV data; check that it actually changed something.
    #     update_url = self.root['operations']['table']['update']['href']
    #     update_url = update_url.format(dbname=base.SETTINGS['dbname'],
    #                                    tablename=self.table_spec['name'])
    #     data = self.get_csvfile_data([(1, 'changed', -1.0)])
    #     response = self.session.post(update_url, data=data, headers=headers)
    #     result = self.check_schema(response)
    #     self.assertEqual(result['nrows'], 3)

    #     response = self.session.get(result['rows']['href'])
    #     result = self.check_schema(response)
    #     rows = result['data']
    #     self.assertEqual(rows[0]['i'], 1)
    #     self.assertEqual(rows[0]['t'], 'changed')
    #     self.assertEqual(rows[2]['i'], 3)
    #     self.assertEqual(rows[2]['t'], 'third')

    #     # Update non-existent row; should not change anything.
    #     data = self.get_csvfile_data([(4, 'this row does not exist', 1.0)])
    #     response = self.session.post(update_url, data=data, headers=headers)
    #     result = self.check_schema(response)
    #     self.assertEqual(result['nrows'], 3)
    #     response = self.session.get(result['rows']['href'])
    #     result = self.check_schema(response)
    #     self.assertEqual(rows, result['data'])

    # def test_index(self):
    #     "Create database and table; create index and test it."

    #     # Create an empty database.
    #     response = self.create_database()
    #     result = self.check_schema(response)

    #     # Add an index definition to the table spec.
    #     table_spec = self.table_spec.copy()
    #     table_spec['indexes'] = [{'unique': True, 'columns': ['t']}]

    #     # Create a table in the database.
    #     url = self.root['operations']['table']['create']['href']
    #     url = url.format(dbname=base.SETTINGS['dbname'],
    #                      tablename=table_spec['name'])
    #     response = self.session.put(url, json=table_spec)
    #     result = self.check_schema(response)
    #     self.assertEqual(len(result['indexes']), 1)

    #     # Add rows.
    #     headers = {'Content-Type': 'text/csv'}
    #     url = self.root['operations']['table']['insert']['href']
    #     url = url.format(dbname=base.SETTINGS['dbname'],
    #                      tablename=self.table_spec['name'])
    #     data = self.get_csvfile_data([(1, 'first row', 1.0),
    #                                   (2, 'second row', 2.0)])
    #     response = self.session.post(url, data=data, headers=headers)
    #     result = self.check_schema(response)
    #     self.assertEqual(result['nrows'], 2)

    #     # Attempt to add rows that violates unique index.
    #     data = self.get_csvfile_data([(3, 'second row', 3.0)])
    #     response = self.session.post(url, data=data, headers=headers)
    #     self.assertEqual(response.status_code, http.client.BAD_REQUEST)

    #     # Add proper third row
    #     data = self.get_csvfile_data([(3, 'third row', 3.0)])
    #     response = self.session.post(url, data=data, headers=headers)
    #     result = self.check_schema(response)
    #     self.assertEqual(result['nrows'], 3)

    # def test_statistics(self):
    #     "Test computation of statistics."

    #     # Create database by file upload
    #     response = self.upload_file()
    #     result = self.check_schema(response)

    #     # Get the table URL and the statistics URL
    #     table_url = result['tables'][0]['href']
    #     response = self.session.get(table_url)
    #     result = self.check_schema(response)
    #     statistics_url = result['statistics']['href']

    #     # Check the statistics
    #     response = self.session.get(statistics_url)
    #     result = self.check_schema(response)


def test_edit_database(settings, database):
    "Test editing database metadata."
    session = settings["session"]
    url = settings["url"]

    # Edit the title.
    title = "New title"
    response = session.post(url, json={"title": title})
    assert response.status_code == http.client.OK
    data = response.json()
    utils.validate_schema(data, settings["db_schema"])
    assert data.get("title") == title

    # Edit the description.
    description = "A description"
    response = session.post(url, json={"description": description})
    assert response.status_code == http.client.OK
    data = response.json()
    utils.validate_schema(data, settings["db_schema"])
    assert data.get("description") == description
    # Same title as before.
    assert data.get("title") == title

    # Rename the database.
    name = "test2"
    response = session.post(url, json={"name": name})
    assert response.status_code == http.client.OK
    data = response.json()
    utils.validate_schema(data, settings["db_schema"])
    assert data["$id"].endswith(name)

    # Delete the renamed database.
    response = session.delete(response.url)
    assert response.status_code == http.client.NO_CONTENT


def test_readonly_database(settings, database):
    "Test setting a database to readonly."
    session = settings["session"]
    url = settings["url"]

    # Set to readonly.
    response = session.post(url + "/readonly")
    assert response.status_code == http.client.OK
    data = response.json()
    utils.validate_schema(data, settings["db_schema"])

    # These items are now True.
    assert data["readonly"]
    assert data["hashes"]

    # Fail to delete the database.
    response = session.delete(url)
    assert response.status_code == http.client.UNAUTHORIZED

    # Set to readwrite.
    response = session.post(url + "/readwrite")
    assert response.status_code == http.client.OK
    data = response.json()
    utils.validate_schema(data, settings["db_schema"])

    # These items are now False.
    assert not data["readonly"]
    assert not data["hashes"]


def test_query_database(settings, database):
    "Test querying a database from a Sqlite3 file."
    session = settings["session"]

    # Query schema.
    response = session.get(f"{settings['BASE_URL']}/api/schema/query/input")
    assert response.status_code == http.client.OK
    query_input_schema = response.json()
    response = session.get(f"{settings['BASE_URL']}/api/schema/query/output")
    assert response.status_code == http.client.OK
    query_output_schema = response.json()

    # Query.
    query = {"select": f'r1 as "r"', "from": "t1"}
    utils.validate_schema(query, query_input_schema)
    response = session.post(f"{settings['BASE_URL']}/api/db/test/query", json=query)
    assert response.status_code == http.client.OK
    data = response.json()
    utils.validate_schema(data, query_output_schema)

    # Bad query.
    query = {"select": None, "from": "t1"}
    response = session.post(f"{settings['BASE_URL']}/api/db/test/query", json=query)
    assert response.status_code == http.client.BAD_REQUEST


def test_view(settings, database):
    "Test creating and using a view."
    session = settings["session"]

    # Create a view.
    view_spec = {
        "name": "v1",
        "query": {"from": "t1", "select": "r1", "where": "i1>=10"},
    }
    utils.validate_schema(view_spec, settings["view_create_schema"])
    response = session.put(f"{settings['BASE_URL']}/api/view/test/v1", json=view_spec)
    assert response.status_code == http.client.OK
    data = response.json()
    utils.validate_schema(data, settings["view_schema"])

    # Check the rows of the view.
    rows_url = data["rows"]["href"]
    response = session.get(rows_url)
    data = response.json()
    utils.validate_schema(data, settings["rows_schema"])
    assert data["nrows"] == 2
    assert len(data["data"]) == data["nrows"]

    # Insert a row into the table, check that view content changes accordingly.
    row = {"data": [{"i": 6, "r1": 1.02, "i1": 3091, "t1": "blopp"}]}
    response = session.post(
        f"{settings['BASE_URL']}/api/table/test/t1/insert", json=row
    )
    data = response.json()
    utils.validate_schema(data, settings["table_schema"])
    response = session.get(rows_url)
    data = response.json()
    utils.validate_schema(data, settings["rows_schema"])
    assert data["nrows"] == 3
    assert len(data["data"]) == data["nrows"]

    # Fail attempt to create a view with uppercase name of already existing view.
    view_spec = {
        "name": "V1",
        "query": {"from": "t1", "select": "r1", "where": "i1>=10"},
    }
    utils.validate_schema(view_spec, settings["view_create_schema"])
    response = session.put(f"{settings['BASE_URL']}/api/view/test/V1", json=view_spec)
    assert response.status_code == http.client.BAD_REQUEST

    # Delete the view.
    response = session.delete(f"{settings['BASE_URL']}/api/view/test/v1")
    assert response.status_code == http.client.NO_CONTENT


def test_user(settings):
    "Test access to the user account."
    session = settings["session"]

    # Current user, check schema.
    response = session.get(
        f"{settings['BASE_URL']}/api/user/{settings['USER_USERNAME']}"
    )
    assert response.status_code == http.client.OK
    data = response.json()
