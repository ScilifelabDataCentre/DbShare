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
    """Get the settings from
    1) defaults
    2) file 'settings.json' in this directory
    """
    # Default values
    result = utils.get_settings(
        BASE_URL="http://localhost:5001", ADMIN_USERNAME=None, ADMIN_APIKEY=None
    )
    # Set up requests session with API key.
    result["session"] = session = requests.Session()
    session.headers.update({"x-apikey": result["ADMIN_APIKEY"]})
    yield result
    result["session"].close()


def test_databases(settings):
    "Test access to the databases."
    response = settings["session"].get(f"{settings['BASE_URL']}/api")
    assert response.status_code == http.client.OK
    data = response.json()
    assert set(data["databases"]) == {"public", "owner", "all"}
    for category in ["public", "owner", "all"]:
        href = data["databases"][category]["href"]
        response = settings["session"].get(href)
        assert response.status_code == http.client.OK
        utils.get_data_check_schema(settings["session"], response)
