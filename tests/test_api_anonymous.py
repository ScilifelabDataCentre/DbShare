"""Test API anonymous access.

Uses the 'requests' package.
"""

import http.client

import requests
import pytest

import utils


@pytest.fixture(scope="module")
def settings():
    "Get the settings from file 'settings.json' in this directory."
    result = utils.get_settings(BASE_URL="http://localhost:5001")
    # Set up requests session.
    result["session"] = session = requests.Session()
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
    assert data["version"] == utils.DBSHARE_VERSION


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
