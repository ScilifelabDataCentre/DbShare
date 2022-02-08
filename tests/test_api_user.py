"""Test API ordinary user access.

Uses the 'requests' package.
"""

import http.client

import requests
import pytest

import dbshare
import utils


@pytest.fixture(scope="module")
def settings():
    """Get the settings from
    1) defaults
    2) file 'settings.json' in this directory
    """
    result = utils.get_settings(
        BASE_URL="http://localhost:5001", USER_USERNAME=None, USER_APIKEY=None
    )
    # Set up requests session with API key.
    result["session"] = session = requests.Session()
    session.headers.update({"x-apikey": result["USER_APIKEY"]})
    yield result
    result["session"].close()


def test_databases(settings):
    "Test access to the databases."
    response = settings["session"].get(f"{settings['BASE_URL']}/api")
    assert response.status_code == http.client.OK
    data = response.json()
    assert set(data["databases"]) == {"public", "owner"}
    for category in ["public", "owner"]:
        href = data["databases"][category]["href"]
        response = settings["session"].get(href)
        assert response.status_code == http.client.OK
        utils.get_data_check_schema(settings["session"], response)

def test_create_database(settings):
    "Test creating and deleting a database."
    # Create it.
    url = f"{settings['BASE_URL']}/api/db/test"
    response = settings["session"].put(url)
    assert response.status_code == http.client.OK
    data = response.json()
    assert len(data["tables"]) == 0
    assert len(data["views"]) == 0

    # Delete it.
    response = settings["session"].delete(url)
    assert response.status_code == http.client.NO_CONTENT

def test_upload_database(settings):
    "Test uploading a database Sqlite3 file."
    # Upload it.
    url = f"{settings['BASE_URL']}/api/db/test"
    with open("test.sqlite3", "rb") as infile:
        headers = {'Content-Type': 'application/x-sqlite3'}
        response = settings["session"].put(url, data=infile, headers=headers)
        assert response.status_code == http.client.OK
    data = response.json()
    assert len(data["tables"]) == 1
    assert len(data["views"]) == 0
    table = data["tables"][0]
    assert table["name"] == "t1"
    assert table["nrows"] == 3

    # Delete it.
    response = settings["session"].delete(url)
    assert response.status_code == http.client.NO_CONTENT
    
def test_query_database(settings):
    "Test querying a database from a Sqlite3 file."
    # Upload it.
    url = f"{settings['BASE_URL']}/api/db/test"
    with open("test.sqlite3", "rb") as infile:
        headers = {'Content-Type': 'application/x-sqlite3'}
        response = settings["session"].put(url, data=infile, headers=headers)
        assert response.status_code == http.client.OK
    data = response.json()
    assert len(data["tables"]) == 1
    assert len(data["views"]) == 0
    table = data["tables"][0]
    assert table["name"] == "t1"
    assert table["nrows"] == 3

    # Query
    response = settings["session"].get(f"{settings['BASE_URL']}/api/schema/query/input")
    assert response.status_code == http.client.OK
    query_input_schema = response.json()
    response = settings["session"].get(f"{settings['BASE_URL']}/api/schema/query/output")
    assert response.status_code == http.client.OK
    query_output_schema = response.json()
    query = {'select': f'r1 as "r"',
             'from': 't1'}
    utils.validate_schema(query, query_input_schema)
    response = settings["session"].post(f"{settings['BASE_URL']}/api/db/test/query", json=query)
    assert response.status_code == http.client.OK
    data = response.json()
    utils.validate_schema(data, query_output_schema)

    # Delete it.
    response = settings["session"].delete(url)
    assert response.status_code == http.client.NO_CONTENT
