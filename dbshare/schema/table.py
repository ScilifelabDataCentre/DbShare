"Table API JSON schema."

from dbshare import constants
from dbshare.schema import definitions


columns = {
    "type": "array",
    "items": {
        "type": "object",
        "properties": {
            "name": {"type": "string"},
            "type": {"type": "string", "enum": ["INTEGER", "REAL", "TEXT", "BLOB"]},
            "primarykey": {"type": "boolean"},
            "notnull": {"type": "boolean"},
            "unique": {"type": "boolean"},
            "statistics": {
                "type": "object",
                "propertyNames": definitions.property_names,
                "additionalProperties": {
                    "type": "object",
                    "properties": {
                        "value": {},
                        "title": {"type": "string"},
                        "info": {},
                    },
                    "required": ["value"],
                    "additionalProperties": False,
                },
            },
        },
        "required": ["name", "type"],
        "additionalProperties": False,
    },
}

indexes = {
    "type": "array",
    "items": {
        "type": "object",
        "properties": {
            "name": {"type": "string"},
            "unique": {"type": "boolean"},
            "columns": {"type": "array", "items": {"type": "string"}},
        },
        "required": ["unique", "columns"],
        "additionalProperties": False,
    },
}

schema = {
    "$id": "/table",
    "$schema": constants.JSON_SCHEMA_URL,
    "title": "Table API JSON schema.",
    "definitions": {"link": definitions.link},
    "type": "object",
    "properties": {
        "$id": {"type": "string", "format": "uri"},
        "timestamp": {"type": "string", "format": "date-time"},
        "name": {"type": "string"},
        "title": {"type": ["string", "null"]},
        "description": {"type": ["string", "null"]},
        "database": {"$ref": "#/definitions/link"},
        "nrows": {"type": "integer", "minimum": 0},
        "rows": {"$ref": "#/definitions/link"},
        "data": {"$ref": "#/definitions/link"},
        "statistics": {"$ref": "#/definitions/link"},
        "columns": columns,
        "indexes": indexes,
    },
    "required": [
        "$id",
        "timestamp",
        "name",
        "database",
        "nrows",
        "rows",
        "data",
        "columns",
        "indexes",
    ],
    "additionalProperties": False,
}

statistics = {
    "$id": "/table/statistics",
    "$schema": constants.JSON_SCHEMA_URL,
    "title": "Table statistics API JSON schema.",
    "definitions": {"link": definitions.link},
    "type": "object",
    "properties": {
        "$id": {"type": "string", "format": "uri"},
        "timestamp": {"type": "string", "format": "date-time"},
        "name": {"type": "string"},
        "nrows": {"type": "integer", "minimum": 0},
        "rows": {"$ref": "#/definitions/link"},
        "data": {"$ref": "#/definitions/link"},
        "href": {"type": "string", "format": "uri"},
        "columns": columns,
    },
    "required": [
        "$id",
        "timestamp",
        "name",
        "nrows",
        "rows",
        "data",
        "href",
        "columns",
    ],
    "additionalProperties": False,
}

create = {
    "$id": "/table/create",
    "$schema": constants.JSON_SCHEMA_URL,
    "title": "Table creation API JSON schema.",
    "type": "object",
    "properties": {
        "name": {"type": "string"},
        "title": {"type": ["string", "null"]},
        "description": {"type": ["string", "null"]},
        "columns": columns,
        "indexes": indexes,
    },
    "required": ["name", "columns"],
}

input = {
    "$id": "/table/input",
    "$schema": constants.JSON_SCHEMA_URL,
    "title": "Table data input API JSON schema.",
    "type": "object",
    "properties": {"data": {"type": "array", "items": {"type": "object"}}},
    "required": ["data"],
}
