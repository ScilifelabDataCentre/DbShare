"API JSON schema for the list of databases."

from dbshare import constants
from dbshare.schema import definitions


schema = {
    "$id": "/dbs",
    "$schema": constants.JSON_SCHEMA_URL,
    "title": "Database list API JSON schema.",
    "definitions": {"user": definitions.user},
    "type": "object",
    "properties": {
        "$id": {"type": "string", "format": "uri"},
        "timestamp": {"type": "string", "format": "date-time"},
        "title": {"type": "string"},
        "user": {"$ref": "#/definitions/user"},
        "total_size": {"type": "integer", "minimum": 0},
        "databases": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "name": {"type": "string"},
                    "title": {"type": ["string", "null"]},
                    "description": {"type": ["string", "null"]},
                    "owner": {"$ref": "#/definitions/user"},
                    "public": {"type": "boolean"},
                    "readonly": {"type": "boolean"},
                    "size": {"type": "integer"},
                    "modified": {"type": "string", "format": "date-time"},
                    "created": {"type": "string", "format": "date-time"},
                    "hashes": definitions.hashes,
                    "href": {"type": "string", "format": "uri"},
                    "operations": definitions.operations,
                },
                "required": [
                    "name",
                    "title",
                    "owner",
                    "public",
                    "readonly",
                    "size",
                    "modified",
                    "created",
                    "href",
                ],
                "additionalProperties": False,
            },
        },
    },
    "required": ["$id", "timestamp", "title", "databases"],
    "additionalProperties": False,
}
