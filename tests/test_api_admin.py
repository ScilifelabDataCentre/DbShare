"""Test API admin user access.

Uses the 'requests' package.
"""

import http.client

import requests
import pytest

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
    yield result
    result["session"].close()


def test_root(settings):
    "Test the root."
    session = settings["session"]

    response = session.get(f"{settings['BASE_URL']}/api")
    assert response.status_code == http.client.OK
    data = response.json()
    url = data["databases"]["public"]["href"]
    response = session.get(url)
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


def test_users(settings):
    "Test access to the user accounts."
    session = settings["session"]

    # Users.
    response = session.get(f"{settings['BASE_URL']}/api/users/all")
    assert response.status_code == http.client.OK
    data = response.json()
    assert len(data["users"]) >= 1

    # A user.
    response = session.get(data["users"][0]["href"])
    assert response.status_code == http.client.OK
