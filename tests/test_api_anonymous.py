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
    """Get the settings from
    1) defaults
    2) file 'settings.json' in this directory
    """
    result = utils.get_settings(BASE_URL="http://localhost:5001")
    # Set up requests session.
    result["session"] = requests.Session()
    yield result
    result["session"].close()


def test_status(settings):
    "Test the presence of the status indicator."
    response = settings["session"].get(f"{settings['BASE_URL']}/status")
    assert response.status_code == http.client.OK
    data = response.json()
    assert "status" in data
    assert data["status"] == "ok"
    assert "n_dbs" in data
    assert "n_users" in data


def test_redirect(settings):
    "Test redirect from web root to API root when accepting only JSON."
    response = settings["session"].get(
        f"{settings['BASE_URL']}", headers={"Accept": "application/json"}
    )
    assert response.status_code == http.client.OK
    assert response.url == f"{settings['BASE_URL']}/api"


def test_root(settings):
    "Test the root and some links from it."
    response = settings["session"].get(f"{settings['BASE_URL']}/api")
    assert response.status_code == http.client.OK
    data = utils.get_data_check_schema(settings["session"], response)
    assert data["version"] == dbshare.__version__
    # Loop over schema.
    for href in utils.get_hrefs(data["schema"]):
        response = settings["session"].get(href)
        assert response.status_code == http.client.OK


def test_databases(settings):
    "Test the public databases, if any."
    response = settings["session"].get(f"{settings['BASE_URL']}/api")
    assert response.status_code == http.client.OK
    data = response.json()
    for href in utils.get_hrefs(data["databases"]):
        response = settings["session"].get(href)
        assert response.status_code == http.client.OK
        data = utils.get_data_check_schema(settings["session"], response)
        for database in data["databases"]:
            response = settings["session"].get(database["href"])
            assert response.status_code == http.client.OK
            utils.get_data_check_schema(settings["session"], response)
