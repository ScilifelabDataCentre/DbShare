"""Test browser anonymous access.

After installing from PyPi using the 'requirements.txt' file, one must do:
$ playwright install

To run while displaying browser window:
$ pytest --headed

Much of the code below was created using the playwright code generation feature:
$ playwright codegen http://localhost:5001/
"""

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
    return utils.get_settings(BASE_URL="http://localhost:5001")


def test_about(settings, page):  # 'page' fixture from 'pytest-playwright'
    "Test access to 'About' pages."
    page.set_default_navigation_timeout(3000)

    page.goto(settings["BASE_URL"])
    page.click("text=About")
    page.click("text=Overview")
    assert page.url == f"{settings['BASE_URL']}/about/documentation/overview"

    page.goto(settings["BASE_URL"])
    page.click("text=About")
    page.click("text=Tutorial")
    assert page.url == f"{settings['BASE_URL']}/about/documentation/tutorial"
    locator = page.locator(".list-group-item > a")
    playwright.sync_api.expect(locator).to_have_count(9)

    page.click('text="Explore an existing database"')
    assert page.url == f"{settings['BASE_URL']}/about/documentation/tutorial-explore"
    page.click('text="Create databases and tables"')
    assert page.url == f"{settings['BASE_URL']}/about/documentation/tutorial-create"
    page.click('text="Modify table contents"')
    assert page.url == f"{settings['BASE_URL']}/about/documentation/tutorial-modify"
    page.click('text="Query database contents"')
    assert page.url == f"{settings['BASE_URL']}/about/documentation/tutorial-query"
    page.click('text="View: a saved query"')
    assert page.url == f"{settings['BASE_URL']}/about/documentation/tutorial-view"
    page.click('text="Download databases and tables"')
    assert page.url == f"{settings['BASE_URL']}/about/documentation/tutorial-download"
    page.click('text="API for programmatic operations"')
    assert page.url == f"{settings['BASE_URL']}/about/documentation/tutorial-api"

    # page.wait_for_timeout(3000)


def test_about_json_schema(settings, page):
    "Test access to 'About' JSON schema pages."
    page.set_default_navigation_timeout(3000)

    page.goto(f"{settings['BASE_URL']}")
    page.click("text=About")
    page.click("text=API JSON schema")
    assert page.url == f"{settings['BASE_URL']}/about/schema"

    page.click("text=root")
    assert page.url == f"{settings['BASE_URL']}/api/schema/root"

    page.go_back()
    page.click("id=dbs")
    assert page.url == f"{settings['BASE_URL']}/api/schema/dbs"
    with open("schema.json", "w") as outfile:
        outfile.write(page.content())

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
    page.set_default_navigation_timeout(3000)

    page.goto(f"{settings['BASE_URL']}")
    page.click("text=demo")
    assert page.url == "http://localhost:5001/db/demo"

    page.click("text=150 rows")
    assert page.url == "http://localhost:5001/table/demo/iris_flower_measurements"

    page.click("text=Query")
    assert page.url == "http://localhost:5001/query/demo?from=iris_flower_measurements"
    page.click("text=Table iris_flower_measurements (150 rows) >> button")
    page.click('textarea[name="select"]')
    page.fill('textarea[name="select"]', "sepal_length")
    page.click('textarea[name="where"]')
    page.fill('textarea[name="where"]', "petal_width > 2.2")
    page.click("text=Execute query")
    assert page.url == "http://localhost:5001/query/demo/rows"
    assert page.locator("#nrows").text_content() == "14"
    locator = page.locator("#rows > tbody > tr")
    playwright.sync_api.expect(locator).to_have_count(14)

    # page.wait_for_timeout(3000)
