"""Test creating, populating, querying, modifying and deleting a table using a browser.

Requires a user account specified in the file 'settings.json'.

After installing from PyPi using the 'requirements.txt' file, one must do:
$ playwright install

To run while displaying browser window:
$ pytest --headed

Much of the code below was created using the playwright code generation feature:
$ playwright codegen http://localhost:5001/
"""

import json
import urllib.parse

import pytest

@pytest.fixture(scope="module")
def settings():
    """Get the settings from
    1) defaults
    2) file 'settings.json' in this directory
    """
    result = {                  # Default values
        "BASE_URL": "http://localhost:5001",
        "USERNAME": None,       # Must be set in 'settings.json'
        "PASSWORD": None,       # Must be set in 'settings.json'
    }

    try:
        with open("settings.json", "rb") as infile:
            result.update(json.load(infile))
    except IOError:
        pass
    for key in ["BASE_URL", "USERNAME", "PASSWORD"]:
        if result.get(key) is None:
            raise KeyError(f"Missing {key} value in settings.")
    # Remove any trailing slash.
    result["BASE_URL"] = result["BASE_URL"].rstrip("/")
    return result

def test_users_databases(settings, page): # 'page' fixture from 'pytest-playwright'
    "Test access to user's databases page."
    page.set_default_timeout(2000)
    page.goto(settings['BASE_URL'])
    page.click("text=Login")
    assert page.url == f"{settings['BASE_URL']}/user/login?"
    page.click("input[name=\"username\"]")
    page.fill("input[name=\"username\"]", settings["USERNAME"])
    page.press("input[name=\"username\"]", "Tab")
    page.fill("input[name=\"password\"]", settings["PASSWORD"])
    page.click("id=login")
    assert page.url == f"{settings['BASE_URL']}/dbs/owner/{settings['USERNAME']}"

    page.click("text=Create")
    assert page.url == f"{settings['BASE_URL']}/db/"

    page.click("input[name=\"name\"]")
    page.fill("input[name=\"name\"]", "test")
    page.click("textarea[name=\"description\"]")
    page.fill("textarea[name=\"description\"]", "test database")
    page.click("button:has-text(\"Create\")")
    assert page.url == f"{settings['BASE_URL']}/db/test"

    page.click("text=Create table")
    assert page.url == f"{settings['BASE_URL']}/table/test"

    page.click("input[name=\"name\"]")
    page.fill("input[name=\"name\"]", "t1")
    page.click("input[name=\"column0name\"]")
    page.fill("input[name=\"column0name\"]", "i")
    page.check("#column0primarykey")
    page.click("input[name=\"column1name\"]")
    page.fill("input[name=\"column1name\"]", "f")
    page.select_option("select[name=\"column1type\"]", "REAL")
    page.click("input[name=\"column2name\"]")
    page.fill("input[name=\"column2name\"]", "s")
    page.select_option("select[name=\"column2type\"]", "TEXT")
    page.click("input[name=\"column3name\"]")
    page.fill("input[name=\"column3name\"]", "r")
    page.select_option("select[name=\"column3type\"]", "REAL")
    page.check("input[name=\"column3notnull\"]")
    page.click("button:has-text(\"Create\")")
    assert page.url == f"{settings['BASE_URL']}/table/test/t1"

    page.click("text=Insert row")
    assert page.url == f"{settings['BASE_URL']}/table/test/t1/row"
    page.click("input[name=\"i\"]")
    page.fill("input[name=\"i\"]", "1")
    page.click("input[name=\"f\"]")
    page.fill("input[name=\"f\"]", "3.0")
    page.click("input[name=\"s\"]")
    page.fill("input[name=\"s\"]", "apa")
    page.click("input[name=\"r\"]")
    page.fill("input[name=\"r\"]", "3.141")
    page.click("button:has-text(\"Insert\")")
    assert page.url == f"{settings['BASE_URL']}/table/test/t1/row"

    page.click("input[name=\"i\"]")
    page.fill("input[name=\"i\"]", "2")
    page.click("input[name=\"f\"]")
    page.click("input[name=\"s\"]")
    page.fill("input[name=\"s\"]", "blah")
    page.click("input[name=\"r\"]")
    page.fill("input[name=\"r\"]", "-1.0")
    page.click("button:has-text(\"Insert\")")
    assert page.url == f"{settings['BASE_URL']}/table/test/t1/row"

    page.click("text=2 rows")
    assert page.url == f"{settings['BASE_URL']}/table/test/t1"

    page.once("dialog", lambda dialog: dialog.accept()) # Callback for next click.
    page.click("text=Delete")
    assert page.url == f"{settings['BASE_URL']}/db/test"

    page.once("dialog", lambda dialog: dialog.accept()) # Callback for next click.
    page.click("text=Delete")
    assert page.url == f"{settings['BASE_URL']}/dbs/owner/{settings['USERNAME']}"

    # page.wait_for_timeout(3000)
