"""Test browser anonymous access.

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
import playwright.sync_api


@pytest.fixture(scope="module")
def settings():
    """Get the settings from
    1) defaults
    2) file 'settings.json' in this directory
    """
    result = {                  # Default values
        "BASE_URL": "http://localhost:5001",
    }

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
    return result

def test_about(settings, page): # 'page' fixture from 'pytest-playwright'
    "Test access to 'About' pages."
    page.set_default_timeout(4000)
    page.goto(settings['BASE_URL'])
    page.click("text=About")
    with page.expect_navigation():
        page.click("text=Overview")
        assert page.url == f"{settings['BASE_URL']}/about/doc/overview"

    page.goto(settings['BASE_URL'])
    page.click("text=About")
    page.click("text=Tutorial")
    assert page.url == f"{settings['BASE_URL']}/about/doc/tutorial"
    page.click("text=Explore a database")
    assert page.url == f"{settings['BASE_URL']}/about/doc/tutorial-explore"
    page.go_back()

    page.click("text=Create and modify a database")
    assert page.url == f"{settings['BASE_URL']}/about/doc/tutorial-create"
    page.go_back()

    page.click("text=Query and view")
    assert page.url == f"{settings['BASE_URL']}/about/doc/tutorial-query"
    page.go_back()

    page.click("text=Using the API")
    assert page.url == f"{settings['BASE_URL']}/about/doc/tutorial-api"
    page.go_back()

    page.click("text=About")
    page.click("text=URL endpoints")
    assert page.url == f"{settings['BASE_URL']}/about/endpoints"

    page.click("text=About")
    page.click("text=Software")
    assert page.url == f"{settings['BASE_URL']}/about/software"

def test_about_json_schema(settings, page):
    "Test access to 'About' JSON schema pages."
    page.set_default_timeout(4000)
    page.goto(f"{settings['BASE_URL']}")
    page.click("text=About")
    page.click("text=API JSON schema")
    assert page.url == f"{settings['BASE_URL']}/about/schema"

    page.click("text=root")
    assert page.url == f"{settings['BASE_URL']}/api/schema/root"
    page.go_back()

    page.click("id=dbs")
    assert page.url == f"{settings['BASE_URL']}/api/schema/dbs"
    page.go_back()

    page.click("id=db")
    assert page.url == f"{settings['BASE_URL']}/api/schema/db"
    page.go_back()

    page.click("text=db/edit")
    assert page.url == f"{settings['BASE_URL']}/api/schema/db/edit"
    page.go_back()

    page.click("text=table")
    assert page.url == f"{settings['BASE_URL']}/api/schema/table"
    page.go_back()

    page.click("text=table/statistics")
    assert page.url == f"{settings['BASE_URL']}/api/schema/table/statistics"
    page.go_back()

    page.click("text=table/create")
    assert page.url == f"{settings['BASE_URL']}/api/schema/table/create"
    page.go_back()

    page.click("text=table/input")
    assert page.url == f"{settings['BASE_URL']}/api/schema/table/input"
    page.go_back()

    page.click("text=view View API JSON schema. >> a")
    assert page.url == f"{settings['BASE_URL']}/api/schema/view"
    page.go_back()

    page.click("text=view/create")
    assert page.url == f"{settings['BASE_URL']}/api/schema/view/create"
    page.go_back()

    page.click("text=rows")
    assert page.url == f"{settings['BASE_URL']}/api/schema/rows"
    page.go_back()

    page.click("text=query/input")
    assert page.url == f"{settings['BASE_URL']}/api/schema/query/input"
    page.go_back()

    page.click("text=query/output")
    assert page.url == f"{settings['BASE_URL']}/api/schema/query/output"
    page.go_back()

    page.click("text=user")
    assert page.url == f"{settings['BASE_URL']}/api/schema/user"
    page.go_back()

    page.click("text=users")
    assert page.url == f"{settings['BASE_URL']}/api/schema/users"
    page.go_back()


def test_demo_database(settings, page):
    "Test access and query of the demo database, which must exist."
    page.set_default_timeout(4000)
    page.goto(f"{settings['BASE_URL']}")
    page.click("text=demo")
    assert page.url == "http://localhost:5001/db/demo"

    page.click("text=150 rows")
    assert page.url == "http://localhost:5001/table/demo/iris_flower_measurements"

    page.click("text=Query")
    assert page.url == "http://localhost:5001/query/demo?from=iris_flower_measurements"
    page.click("text=Table iris_flower_measurements (150 rows) >> button")
    page.click("textarea[name=\"select\"]")
    page.fill("textarea[name=\"select\"]", "sepal_length")
    page.click("textarea[name=\"where\"]")
    page.fill("textarea[name=\"where\"]", "petal_width > 2.2")
    page.click("text=Execute query")
    assert page.url == "http://localhost:5001/query/demo/rows"
    assert page.locator("#nrows").text_content() == "14"
    locator = page.locator("#rows > tbody > tr")
    playwright.sync_api.expect(locator).to_have_count(14)

    # page.wait_for_timeout(3000)
