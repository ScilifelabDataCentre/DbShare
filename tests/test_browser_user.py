"""Test operations for an ordinary logged-in user in a browser.

Requires a user account specified in the file 'settings.json' given by
- USER_USERNAME
- USER_PASSWORD

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
        BASE_URL="http://localhost:5001", USER_USERNAME=None, USER_PASSWORD=None
    )


def login_user(settings, page):
    "Login to the system as ordinary user."
    page.goto(settings["BASE_URL"])
    page.click("text=Login")
    assert page.url == f"{settings['BASE_URL']}/user/login?"
    page.click('input[name="username"]')
    page.fill('input[name="username"]', settings["USER_USERNAME"])
    page.press('input[name="username"]', "Tab")
    page.fill('input[name="password"]', settings["USER_PASSWORD"])
    page.click("id=login")
    assert page.url == f"{settings['BASE_URL']}/dbs/owner/{settings['USER_USERNAME']}"


def test_table_data(settings, page):  # 'page' fixture from 'pytest-playwright'
    "Test login, creating a table, inserting data 'by hand'."
    login_user(settings, page)

    # Create a database 'test'.
    page.click("text=Create")
    assert page.url == f"{settings['BASE_URL']}/db/"
    page.click('input[name="name"]')
    page.fill('input[name="name"]', "test")
    page.click('textarea[name="description"]')
    page.fill('textarea[name="description"]', "test database")
    page.click('button:has-text("Create")')
    assert page.url == f"{settings['BASE_URL']}/db/test"

    # Create a table 't1'.
    page.click("text=Create table")
    assert page.url == f"{settings['BASE_URL']}/table/test"
    page.click('input[name="name"]')
    page.fill('input[name="name"]', "t1")
    page.click('input[name="column0name"]')
    page.fill('input[name="column0name"]', "i")
    page.check("#column0primarykey")
    page.click('input[name="column1name"]')
    page.fill('input[name="column1name"]', "f")
    page.select_option('select[name="column1type"]', "REAL")
    page.click('input[name="column2name"]')
    page.fill('input[name="column2name"]', "s")
    page.select_option('select[name="column2type"]', "TEXT")
    page.click('input[name="column3name"]')
    page.fill('input[name="column3name"]', "r")
    page.select_option('select[name="column3type"]', "REAL")
    page.check('input[name="column3notnull"]')
    page.click('button:has-text("Create")')
    assert page.url == f"{settings['BASE_URL']}/table/test/t1"

    # Insert a row into the table.
    page.click("text=Insert row")
    assert page.url == f"{settings['BASE_URL']}/table/test/t1/row"
    page.click('input[name="i"]')
    page.fill('input[name="i"]', "1")
    page.click('input[name="f"]')
    page.fill('input[name="f"]', "3.0")
    page.click('input[name="s"]')
    page.fill('input[name="s"]', "apa")
    page.click('input[name="r"]')
    page.fill('input[name="r"]', "3.141")
    page.click('button:has-text("Insert")')
    assert page.url == f"{settings['BASE_URL']}/table/test/t1/row"

    # Insert another row into the table.
    page.click('input[name="i"]')
    page.fill('input[name="i"]', "2")
    page.click('input[name="f"]')
    page.click('input[name="s"]')
    page.fill('input[name="s"]', "blah")
    page.click('input[name="r"]')
    page.fill('input[name="r"]', "-1.0")
    page.click('button:has-text("Insert")')
    assert page.url == f"{settings['BASE_URL']}/table/test/t1/row"

    # Delete the table.
    page.click("text=2 rows")
    table_url = f"{settings['BASE_URL']}/table/test/t1"
    assert page.url == table_url
    page.once("dialog", lambda dialog: dialog.accept())  # Callback for next click.
    page.click("text=Delete")
    assert page.url == f"{settings['BASE_URL']}/db/test"
    page.goto(table_url)
    locator = page.locator("text=No such table")
    playwright.sync_api.expect(locator).to_have_count(1)

    # Delete the database.
    page.once("dialog", lambda dialog: dialog.accept())  # Callback for next click.
    page.click("text=Delete")
    assert page.url == f"{settings['BASE_URL']}/dbs/owner/{settings['USER_USERNAME']}"


def test_table_csv(settings, page):  # 'page' fixture from 'pytest-playwright'
    "Test login, creating a table, inserting data from a CSV file."
    login_user(settings, page)

    # Create a database 'test'.
    page.click("text=Create")
    assert page.url == f"{settings['BASE_URL']}/db/"
    page.click('input[name="name"]')
    page.fill('input[name="name"]', "test")
    page.click('button:has-text("Create")')
    assert page.url == f"{settings['BASE_URL']}/db/test"

    # Create a table 't1'.
    page.click("text=Create table")
    assert page.url == f"{settings['BASE_URL']}/table/test"
    page.click('input[name="name"]')
    page.fill('input[name="name"]', "t1")
    page.click('input[name="column0name"]')
    page.fill('input[name="column0name"]', "i")
    page.check("#column0primarykey")
    page.click('input[name="column1name"]')
    page.fill('input[name="column1name"]', "r")
    page.select_option('select[name="column1type"]', "REAL")
    page.click('input[name="column2name"]')
    page.fill('input[name="column2name"]', "j")
    page.click('input[name="column3name"]')
    page.fill('input[name="column3name"]', "t")
    page.select_option('select[name="column3type"]', "TEXT")
    page.check('input[name="column3notnull"]')
    page.click('button:has-text("Create")')
    assert page.url == f"{settings['BASE_URL']}/table/test/t1"

    # Insert data from file.
    page.click("text=Insert from file")
    assert page.url == "http://localhost:5001/table/test/t1/insert"
    with page.expect_file_chooser() as fc_info:
        page.click('input[name="csvfile"]')
    file_chooser = fc_info.value
    file_chooser.set_files("test.csv")
    page.click("text=Insert from CSV file")
    assert page.url == "http://localhost:5001/table/test/t1"

    page.click("text=Database test")
    assert page.url == f"{settings['BASE_URL']}/db/test"

    # Query the database.
    page.click("text=Query")
    assert page.url == "http://localhost:5001/query/test"
    page.click('textarea[name="select"]')
    page.fill('textarea[name="select"]', "i,r")
    page.click('textarea[name="from"]')
    page.fill('textarea[name="from"]', "t1")
    page.click('textarea[name="where"]')
    page.fill('textarea[name="where"]', 't = "blah"')
    page.click("text=Execute query")
    assert page.url == "http://localhost:5001/query/test/rows"
    assert page.locator("#nrows").text_content() == "1"
    locator = page.locator("#rows > tbody > tr")
    playwright.sync_api.expect(locator).to_have_count(1)

    # Modify the query.
    page.click("text=Edit query")
    assert page.url.startswith("http://localhost:5001/query/test")
    page.click('textarea[name="where"]')
    page.fill('textarea[name="where"]', "j = 3")
    page.click("text=Execute query")
    assert page.url == "http://localhost:5001/query/test/rows"
    assert page.locator("#nrows").text_content() == "2"
    locator = page.locator("#rows > tbody > tr")
    playwright.sync_api.expect(locator).to_have_count(2)

    # Delete the database.
    page.click("text=Database test")
    assert page.url == "http://localhost:5001/db/test"
    page.once("dialog", lambda dialog: dialog.accept())  # Callback for next click.
    page.click("text=Delete")
    assert page.url == f"{settings['BASE_URL']}/dbs/owner/{settings['USER_USERNAME']}"


def test_db_upload(settings, page):
    "Test uploading a Sqlite3 database file."
    login_user(settings, page)

    # Upload database file.
    page.click("text=Upload")
    assert page.url == "http://localhost:5001/dbs/upload"
    page.once("filechooser", lambda fc: fc.set_files("test.sqlite3"))
    page.click('input[name="sqlite3file"]')
    page.click("text=Upload SQLite3 file")
    assert page.url == "http://localhost:5001/db/test"
    page.click("text=3 rows")
    assert page.url == "http://localhost:5001/table/test/t1"
    locator = page.locator("#rows > tbody > tr")
    playwright.sync_api.expect(locator).to_have_count(3)
    page.click('a[role="button"]:has-text("Schema")')
    assert page.url == "http://localhost:5001/table/test/t1/schema"
    locator = page.locator("#columns > tbody > tr")
    playwright.sync_api.expect(locator).to_have_count(7)

    # Delete the database.
    page.click("text=Database test")
    assert page.url == "http://localhost:5001/db/test"
    page.once("dialog", lambda dialog: dialog.accept())  # Callback for next click.
    page.click("text=Delete")
    assert page.url == f"{settings['BASE_URL']}/dbs/owner/{settings['USER_USERNAME']}"


def test_view(settings, page):
    "Test view creation, based on a table in an uploaded Sqlite3 database file."
    login_user(settings, page)

    page.click("text=Upload")
    assert page.url == "http://localhost:5001/dbs/upload"
    page.once("filechooser", lambda fc: fc.set_files("test.sqlite3"))
    page.click('input[name="sqlite3file"]')
    page.click("text=Upload SQLite3 file")
    assert page.url == "http://localhost:5001/db/test"

    # Create the view.
    page.click("text=Query")
    assert page.url == "http://localhost:5001/query/test"
    page.click('textarea[name="select"]')
    page.fill('textarea[name="select"]', "i, r1")
    page.click("textarea[name=\"from\"]")
    page.fill("textarea[name=\"from\"]", "t1")
    page.click("textarea[name=\"where\"]")
    page.fill("textarea[name=\"where\"]", "i2 < 0")
    page.click("text=Execute query")
    assert page.url == "http://localhost:5001/query/test/rows"
    page.click("text=Create view")
    page.click('input[name="name"]')
    page.fill('input[name="name"]', "v1")
    page.click("button:has-text(\"Create\")")
    page.wait_for_timeout(3000)
    locator = page.locator("#rows > tbody > tr")
    playwright.sync_api.expect(locator).to_have_count(2)

    # Delete the database.
    page.click("text=Database test")
    assert page.url == "http://localhost:5001/db/test"
    page.once("dialog", lambda dialog: dialog.accept())  # Callback for next click.
    page.click("text=Delete")
    assert page.url == f"{settings['BASE_URL']}/dbs/owner/{settings['USER_USERNAME']}"

    # page.wait_for_timeout(3000)
