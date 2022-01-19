"""Test browser access.

To run while displaying browser window:
$ pytest --headed

Much of the code below was created using the playwright code generation feature:
$ playwright codegen http://localhost:5001/

Requires:
$ pip install pytest
$ pip install playwright
$ playwright install
$ pip install pytest-playwright
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
    result = {
        "BASE_URL": "http://localhost:5001/",
        "USERNAME": None,
        "PASSWORD": None
    }

    try:
        with open("settings.json", "rb") as infile:
            result.update(json.load(infile))
    except IOError:
        pass
    for key in result:
        if result.get(key) is None:
            raise KeyError(f"Missing {key} value in settings.")
    # Ensure trailing slash.
    result["BASE_URL"] = result["BASE_URL"].rstrip("/") + "/"
    return result

def test_about(settings, page): # 'page' fixture from 'pytest-playwright'
    "Test access to 'About' pages."
    url = f"{settings['BASE_URL']}"
    page.goto(url)
    # Click text=About
    page.click("text=About")
    # Click text=Overview
    page.click("text=Overview")
    assert page.url == "http://localhost:5001/about/doc/overview"
    # Go to http://localhost:5001/
    page.goto("http://localhost:5001/")
    # Click text=About
    page.click("text=About")
    # Click text=Tutorial
    page.click("text=Tutorial")
    assert page.url == "http://localhost:5001/about/doc/tutorial"
    # Click text=Explore a database
    page.click("text=Explore a database")
    assert page.url == "http://localhost:5001/about/doc/tutorial-explore"
    # Go back to previous page
    page.go_back()

    # Click text=Create and modify a database
    with page.expect_navigation():
        page.click("text=Create and modify a database")
        assert page.url == "http://localhost:5001/about/doc/tutorial-create"
    # Go back to previous page
    page.go_back()

    # Click text=Query and view
    with page.expect_navigation():
        page.click("text=Query and view")
        assert page.url == "http://localhost:5001/about/doc/tutorial-query"
    # Go back to previous page
    page.go_back()

    # Click text=Using the API
    with page.expect_navigation():
        page.click("text=Using the API")
        assert page.url == "http://localhost:5001/about/doc/tutorial-api"
    # Go back to previous page
    page.go_back()

    # Click text=About
    page.click("text=About")
    # Click text=URL endpoints
    page.click("text=URL endpoints")
    assert page.url == "http://localhost:5001/about/endpoints"

    # Click text=About
    page.click("text=About")
    # Click text=Software
    page.click("text=Software")
    assert page.url == "http://localhost:5001/about/software"
    # page.wait_for_timeout(5000)

def test_about_json_schema(settings, page):
    "Test access to 'About' JSON schema pages."
    url = f"{settings['BASE_URL']}"
    page.goto(url)
    # Click text=About
    page.click("text=About")
    # Click text=API JSON schema
    page.click("text=API JSON schema")
    assert page.url == "http://localhost:5001/about/schema"

    # Click text=root
    page.click("text=root")
    assert page.url == "http://localhost:5001/api/schema/root"
    # Go back to previous page
    page.go_back()

    # Click text=dbs Database list API JSON schema. >> a
    page.click("text=dbs Database list API JSON schema. >> a")
    assert page.url == "http://localhost:5001/api/schema/dbs"
    # Go back to previous page
    page.go_back()

    # Click text=db Database API JSON schema. >> a
    page.click("text=db Database API JSON schema. >> a")
    assert page.url == "http://localhost:5001/api/schema/db"
    # Go back to previous page
    page.go_back()

    # Click text=db/edit
    page.click("text=db/edit")
    assert page.url == "http://localhost:5001/api/schema/db/edit"
    # Go back to previous page
    page.go_back()

    # Click text=table
    page.click("text=table")
    assert page.url == "http://localhost:5001/api/schema/table"
    # Go back to previous page
    page.go_back()

    # Click text=table/statistics
    page.click("text=table/statistics")
    assert page.url == "http://localhost:5001/api/schema/table/statistics"
    # Go back to previous page
    page.go_back()

    # Click text=table/create
    page.click("text=table/create")
    assert page.url == "http://localhost:5001/api/schema/table/create"
    # Go back to previous page
    page.go_back()

    # Click text=table/input
    page.click("text=table/input")
    assert page.url == "http://localhost:5001/api/schema/table/input"
    # Go back to previous page
    page.go_back()

    # Click text=view View API JSON schema. >> a
    page.click("text=view View API JSON schema. >> a")
    assert page.url == "http://localhost:5001/api/schema/view"
    # Go back to previous page
    page.go_back()

    # Click text=view/create
    page.click("text=view/create")
    assert page.url == "http://localhost:5001/api/schema/view/create"
    # Go back to previous page
    page.go_back()

    # Click text=rows
    page.click("text=rows")
    assert page.url == "http://localhost:5001/api/schema/rows"
    # Go back to previous page
    page.go_back()

    # Click text=query/input
    page.click("text=query/input")
    assert page.url == "http://localhost:5001/api/schema/query/input"
    # Go back to previous page
    page.go_back()

    # Click text=query/output
    page.click("text=query/output")
    assert page.url == "http://localhost:5001/api/schema/query/output"
    # Go back to previous page
    page.go_back()

    # Click text=user
    page.click("text=user")
    assert page.url == "http://localhost:5001/api/schema/user"
    # Go back to previous page
    page.go_back()

    # Click text=users
    page.click("text=users")
    assert page.url == "http://localhost:5001/api/schema/users"
    # Go back to previous page
    page.go_back()
