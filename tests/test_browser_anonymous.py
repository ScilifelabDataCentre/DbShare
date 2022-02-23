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
    "Get the settings from file 'settings.json' in this directory."
    return utils.get_settings(BASE_URL="http://localhost:5001")


def test_about(settings, page):  # 'page' fixture from 'pytest-playwright'
    "Test access to 'About' pages."
    page.set_default_navigation_timeout(3000)

    page.goto(settings["BASE_URL"])
    page.click("text=About")
    page.click("text=Contact")
    assert page.url == f"{settings['BASE_URL']}/about/contact"

    page.goto(settings["BASE_URL"])
    page.click("text=About")
    page.click("text=Personal data policy")
    assert page.url == f"{settings['BASE_URL']}/about/gdpr"

    page.goto(settings["BASE_URL"])
    page.click("text=About")
    page.click("text=Software")
    assert page.url == f"{settings['BASE_URL']}/about/software"

    # page.wait_for_timeout(3000)


def test_documentation(settings, page):
    "Test access to 'Documentation' pages."
    page.set_default_navigation_timeout(3000)

    page.goto(settings["BASE_URL"])
    page.click("text=Documentation")
    page.click("text=Overview")
    assert page.url == f"{settings['BASE_URL']}/documentation/overview"
    locator = page.locator(".list-group-item > a")
    playwright.sync_api.expect(locator).to_have_count(3)

    page.goto(settings["BASE_URL"])
    page.click("text=Documentation")
    page.click("text=Tutorial")
    assert page.url == f"{settings['BASE_URL']}/documentation/tutorial"

    page.click('text="Explore an existing database"')
    assert page.url == f"{settings['BASE_URL']}/documentation/tutorial-explore"
    page.click('text="Create databases and tables"')
    assert page.url == f"{settings['BASE_URL']}/documentation/tutorial-create"
    page.click('text="Modify table contents"')
    assert page.url == f"{settings['BASE_URL']}/documentation/tutorial-modify"
    page.click('text="Query database contents"')
    assert page.url == f"{settings['BASE_URL']}/documentation/tutorial-query"
    page.click('text="View: a saved query"')
    assert page.url == f"{settings['BASE_URL']}/documentation/tutorial-view"
    page.click('text="Download databases and tables"')
    assert page.url == f"{settings['BASE_URL']}/documentation/tutorial-download"
    page.click('text="API introduction and example"')
    assert page.url == f"{settings['BASE_URL']}/documentation/api-intro"

    # page.wait_for_timeout(3000)


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
