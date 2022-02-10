"""Test API admin user access.

Uses the 'requests' package.
"""

import http.client

import requests
import pytest

import dbshare
import utils


@pytest.fixture(scope="module")
def settings():
    "Get the settings from file 'settings.json' in this directory."
    result = utils.get_settings(
        BASE_URL="http://localhost:5001", ADMIN_USERNAME=None, ADMIN_APIKEY=None
    )
    # Set up requests session with API key.
    result["session"] = session = requests.Session()
    session.headers.update({"x-apikey": result["ADMIN_APIKEY"]})
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
    yield result
    result["session"].close()


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

    # All database categories.
    response = session.get(f"{settings['BASE_URL']}/api")
    assert response.status_code == http.client.OK
    data = response.json()
    assert set(data["databases"]) == {"public", "owner", "all"}
    for category in data["databases"]:
        href = data["databases"][category]["href"]
        response = session.get(href)
        assert response.status_code == http.client.OK
        utils.validate_schema(response.json(), settings["dbs_schema"])
    

def test_users(settings):
    "Test access to the user accounts."
    session = settings["session"]

    # Users, check schema.
