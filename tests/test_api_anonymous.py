"""Test API anonymous access.

Uses the 'requests' package.
"""

import http.client
import json

import requests
import pytest

import dbshare
from utils import *


@pytest.fixture(scope="module")
def settings():
    """Get the settings from
    1) defaults
    2) file 'settings.json' in this directory
    """
    # Default values
    result = {"BASE_URL": "http://localhost:5001"}
    try:
        with open("settings.json", "rb") as infile:
            result.update(json.load(infile))
    except IOError:
        pass
    for key in ["BASE_URL"]:
        if result.get(key) is None:
            raise KeyError(f"Missing {key} value in settings.")
    # Remove any trailing slash.
    result["BASE_URL"] = result["BASE_URL"].rstrip("/")
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


def test_root(settings):
    "Test the root."
    response = settings["session"].get(f"{settings['BASE_URL']}/api")
    assert response.status_code == http.client.OK
    data = response.json()
    assert "version" in data
    assert data["version"] == dbshare.__version__
    response = settings["session"].get(response.links["schema"]["url"])
    validate_schema(data, response.json())
    for href in get_hrefs(data["databases"]):
        response = settings["session"].get(href)
        assert response.status_code == http.client.OK
    for href in get_hrefs(data["schema"]):
        response = settings["session"].get(href)
        assert response.status_code == http.client.OK
