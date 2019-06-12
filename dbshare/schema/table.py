"JSON schema for the table API."

from . import definitions
from . import visualization
from . import column
from .. import constants


output = {
    '$id': constants.SCHEMA_BASE_URL + 'table',
    '$schema': constants.SCHEMA_SCHEMA_URL,
    'title': 'JSON schema for the table API output.',
    'definitions': definitions.schema,
    'type': 'object',
    'properties': {
        '$id': {'type': 'string', 'format': 'uri'},
        'name': {'type': 'string'},
        'title': {'type': ['string', 'null']},
        'description': {'type': ['string', 'null']},
        'database': {'$ref': '#/definitions/link'},
        'nrows': {'type': 'integer', 'minimum': 0},
        'rows': {'$ref': '#/definitions/link'},
        'data': {'$ref': '#/definitions/link'},
        'visualizations': {
            'type': 'array',
            'items': visualization.schema},
        'columns': {
            'type': 'array',
            'items': column.spec},
        'timestamp': {'type': 'string', 'format': 'timestamp'}
    },
    'required': [
        '$id',
        'name', 
        'database',
        'nrows',
        'rows',
        'data',
        'visualizations',
        'columns',
        'timestamp'
    ]
}

create = {
    '$id': 'https://dbshare.scilifelab.se/api/schema/table_create',
    '$schema': 'http://json-schema.org/draft-07/schema#',
    'title': 'JSON schema for table creation API.',
    'type': 'object',
    'properties': {
        'name': {'type': 'string'},
        'title': {'type': ['string', 'null']},
        'description': {'type': ['string', 'null']},
        'columns': {
            'type': 'array',
            'items': column.spec}
    },
    'required': [
        'name', 
        'columns'
    ]
}

input = {
    '$id': 'https://dbshare.scilifelab.se/api/schema/table_data',
    '$schema': 'http://json-schema.org/draft-07/schema#',
    'title': 'JSON schema for the table API output.',
    'type': 'object',
    'properties': {
        'data': {
            'type': 'array',
            'items': {'type': 'object'}
        }
    },
    'required': [
        'data'
    ]
}
