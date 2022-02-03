"Utility functions for the tests."

import http.client
import json

import jsonschema


def get_settings(**defaults):
    "Update the default settings by the contents of the 'settings.json' file."
    result = defaults.copy()
    with open("settings.json", "rb") as infile:
        data = json.load(infile)
    for key in result:
        try:
            result[key] = data[key]
        except KeyError:
            pass
        if result.get(key) is None:
            raise KeyError(f"Missing {key} value in settings.")
    # Remove any trailing slash in the base URL.
    result["BASE_URL"] = result["BASE_URL"].rstrip("/")
    return result


def get_data_check_schema(session, response):
    """Check that there is a schema linked in the response headers,
    and that the response JSON data matches that schema.
    Return the response JSON.
    """
    result = response.json()
    url = response.links["schema"]["url"]
    r = session.get(url)
    assert r.status_code == http.client.OK
    jsonschema.validate(
        instance=result,
        schema=r.json(),
        format_checker=jsonschema.draft7_format_checker,
    )
    return result


def validate_schema(instance, schema):
    "Validate the given JSON instance versus the given JSON schema."


def get_hrefs(data):
    """Traversing the data recursively, return the list of values
    for all 'href' keys in the dictionary.
    If a 'href' value is not a string, then ignore it.
    """
    result = []
    if isinstance(data, list):
        for value in data:
            result.append(get_hrefs(value))
    elif isinstance(data, dict):
        for key, value in data.items():
            if key == "href":
                if isinstance(value, str):
                    result.append(value)
            elif isinstance(value, (list, dict)):
                result.extend(get_hrefs(value))
    return result
