"""Test API anonymous access.

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
    result = utils.get_settings(BASE_URL="http://localhost:5001")
    # Set up requests session.
    result["session"] = session = requests.Session()
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


def test_status(settings):
    "Test the presence of the status indicator."
    session = settings["session"]

    response = session.get(f"{settings['BASE_URL']}/status")
    assert response.status_code == http.client.OK
    data = response.json()
    assert "status" in data
    assert data["status"] == "ok"
    assert "n_dbs" in data
    assert "n_users" in data


def test_redirect(settings):
    "Test redirect from web root to API root when accepting only JSON."
    session = settings["session"]

    response = session.get(
        f"{settings['BASE_URL']}", headers={"Accept": "application/json"}
    )
    assert response.status_code == http.client.OK
    assert response.url == f"{settings['BASE_URL']}/api"


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
    "Test the public databases, if any."
    session = settings["session"]

    response = session.get(f"{settings['BASE_URL']}/api")
    assert response.status_code == http.client.OK
    data = response.json()
    assert set(data["databases"]) == {
        "public",
    }
    for category in data["databases"]:
        href = data["databases"][category]["href"]
        response = session.get(href)
        assert response.status_code == http.client.OK
        utils.validate_schema(response.json(), settings["dbs_schema"])
