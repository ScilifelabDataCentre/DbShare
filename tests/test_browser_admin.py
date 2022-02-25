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
    "Get the settings from file 'settings.json' in this directory."
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
    assert page.url == f"{settings['BASE_URL']}/"


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


def test_create_user(settings, page):
    "Test creating, modifying and deleting a user."
    login_user(settings, page)
    page.goto(settings["BASE_URL"])
    page.click("text=Admin")
    page.click("text=Create user")

    # Create user account.
    assert page.url == f"{settings['BASE_URL']}/user/create"
    page.click('input[name="username"]')
    page.fill('input[name="username"]', "testing")
    page.press('input[name="username"]', "Tab")
    page.fill('input[name="email"]', "testing@dummy.org")
    page.press('input[name="email"]', "Tab")
    page.fill('input[name="password"]', "testing123")
    page.click('button:has-text("Create")')
    assert page.url == f"{settings['BASE_URL']}/user/display/testing"

    # Disable user account.
    assert page.locator("#status").inner_text() == "enabled"
    page.click('button:has-text("Disable")')
    assert page.locator("#status").inner_text() == "disabled"
    page.click('button:has-text("Enable")')
    assert page.locator("#status").inner_text() == "enabled"

    # Try logging out, and then login to the created user.
    page.click(f"text=User {settings['ADMIN_USERNAME']}")
    page.click("text=Logout")
    page.click("text=Login")
    assert page.url == f"{settings['BASE_URL']}/user/login?"
    page.click('input[name="username"]')
    page.fill('input[name="username"]', "testing")
    page.press('input[name="username"]', "Tab")
    page.fill('input[name="password"]', "testing123")
    page.click("id=login")
    assert page.url == f"{settings['BASE_URL']}/"
    page.click("text=User testing")
    page.click("text=Logout")

    # Delete user account.
    login_user(settings, page)
    page.goto(f"{settings['BASE_URL']}/user/display/testing")
    page.once("dialog", lambda dialog: dialog.accept())  # Callback for next click.
    page.click('button:has-text("Delete")')
    assert page.url == f"{settings['BASE_URL']}/user/users"

    # page.wait_for_timeout(3000)
