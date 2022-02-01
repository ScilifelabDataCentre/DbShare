"Utility functions for the tests."

import jsonschema


def validate_schema(instance, schema):
    "Validate the given JSON instance versus the given JSON schema."
    jsonschema.validate(
        instance=instance,
        schema=schema,
        format_checker=jsonschema.draft7_format_checker,
    )


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
