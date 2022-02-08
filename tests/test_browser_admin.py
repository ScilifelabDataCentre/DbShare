"""Test operations for an admin user in a browser.

Requires a user account specified in the file 'settings.json' given by
- ADMIN_USERNAME
- ADMIN_PASSWORD

After installing from PyPi using the 'requirements.txt' file, one must do:
$ playwright install

To run while displaying browser window:
$ pytest --headed

Much of the code below was created using the playwright code generation feature:
$ playwright codegen http://localhost:5001/
"""

import http.client
import urllib.parse

import pytest
import playwright.sync_api

import utils


@pytest.fixture(scope="module")
def settings():
    """Get the settings from
    1) defaults
    2) file 'settings.json' in this directory
    """
    return utils.get_settings(
        BASE_URL="http://localhost:5001", ADMIN_USERNAME=None, ADMIN_PASSWORD=None
    )


def login_user(settings, page):
    "Login to the system as admin user."
    page.goto(settings["BASE_URL"])
    page.click("text=Login")
    assert page.url == f"{settings['BASE_URL']}/user/login?"
    page.click('input[name="username"]')
    page.fill('input[name="username"]', settings["ADMIN_USERNAME"])
    page.press('input[name="username"]', "Tab")
    page.fill('input[name="password"]', settings["ADMIN_PASSWORD"])
    page.click("id=login")
    assert page.url == f"{settings['BASE_URL']}/dbs/owner/{settings['ADMIN_USERNAME']}"

def test_admin_pages(settings, page):
    "Test admin-pecific pages."
    login_user(settings, page)
    page.goto(settings["BASE_URL"])
    page.click("text=Admin")
    page.click("text=All databases")
    page.click("text=Admin")
    page.click("text=All users")
    page.click("text=Admin")
    page.click("text=Settings")
