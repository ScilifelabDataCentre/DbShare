"""Test browser anonymous access.

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
    page.set_default_timeout(4000)
    page.goto(settings['BASE_URL'])
    page.click("text=About")
    with page.expect_navigation():
        page.click("text=Overview")
        assert page.url == f"{settings['BASE_URL']}about/doc/overview"

    page.goto(settings['BASE_URL'])
    page.click("text=About")
    with page.expect_navigation():
        page.click("text=Tutorial")
        assert page.url == f"{settings['BASE_URL']}about/doc/tutorial"
    with page.expect_navigation():
        page.click("text=Explore a database")
        assert page.url == f"{settings['BASE_URL']}about/doc/tutorial-explore"
    page.go_back()

    with page.expect_navigation():
        page.click("text=Create and modify a database")
        assert page.url == f"{settings['BASE_URL']}about/doc/tutorial-create"
    page.go_back()

    with page.expect_navigation():
        page.click("text=Query and view")
        assert page.url == f"{settings['BASE_URL']}about/doc/tutorial-query"
    page.go_back()

    with page.expect_navigation():
        page.click("text=Using the API")
        assert page.url == f"{settings['BASE_URL']}about/doc/tutorial-api"
    page.go_back()

    page.click("text=About")
    page.click("text=URL endpoints")
    assert page.url == f"{settings['BASE_URL']}about/endpoints"

    page.click("text=About")
    page.click("text=Software")
    assert page.url == f"{settings['BASE_URL']}about/software"

def test_about_json_schema(settings, page):
    "Test access to 'About' JSON schema pages."
    page.set_default_timeout(4000)
    page.goto(f"{settings['BASE_URL']}")
    page.click("text=About")
    page.click("text=API JSON schema")
    assert page.url == f"{settings['BASE_URL']}about/schema"

    page.click("text=root")
    assert page.url == f"{settings['BASE_URL']}api/schema/root"
    page.go_back()

    page.click("id=dbs")
    assert page.url == f"{settings['BASE_URL']}api/schema/dbs"
    page.go_back()

    page.click("id=db")
    assert page.url == f"{settings['BASE_URL']}api/schema/db"
    page.go_back()

    page.click("text=db/edit")
    assert page.url == f"{settings['BASE_URL']}api/schema/db/edit"
    page.go_back()

    page.click("text=table")
    assert page.url == f"{settings['BASE_URL']}api/schema/table"
    page.go_back()

    page.click("text=table/statistics")
    assert page.url == f"{settings['BASE_URL']}api/schema/table/statistics"
    page.go_back()

    page.click("text=table/create")
    assert page.url == f"{settings['BASE_URL']}api/schema/table/create"
    page.go_back()

    page.click("text=table/input")
    assert page.url == f"{settings['BASE_URL']}api/schema/table/input"
    page.go_back()

    page.click("text=view View API JSON schema. >> a")
    assert page.url == f"{settings['BASE_URL']}api/schema/view"
    page.go_back()

    page.click("text=view/create")
    assert page.url == f"{settings['BASE_URL']}api/schema/view/create"
    page.go_back()

    page.click("text=rows")
    assert page.url == f"{settings['BASE_URL']}api/schema/rows"
    page.go_back()

    page.click("text=query/input")
    assert page.url == f"{settings['BASE_URL']}api/schema/query/input"
    page.go_back()

    page.click("text=query/output")
    assert page.url == f"{settings['BASE_URL']}api/schema/query/output"
    page.go_back()

    page.click("text=user")
    assert page.url == f"{settings['BASE_URL']}api/schema/user"
    page.go_back()

    page.click("text=users")
    assert page.url == f"{settings['BASE_URL']}api/schema/users"
    page.go_back()

    # page.wait_for_timeout(3000)
