"Query API JSON schema."

from .. import constants


query = {
    'type': 'object',
    'properties': {
        'select': {'type': 'string'},
        'from': {'type': 'string'},
        'where': {'type': ['string', 'null']},
        'orderby': {'type': ['string', 'null']},
        'limit': {
            'oneOf': [
                {'type': 'null'},
                {'type': 'integer', 'minimum': 1}
            ]
        },
        'offset': {
            'oneOf': [
                {'type': 'null'},
                {'type': 'integer', 'minimum': 1}
            ]
        },
        'columns': {
            'type': 'array',
            'items': {'type': 'string'}
        }
    },
    'required': [
        'select',
        'from'
    ],
    'additionalProperties': False
}

input = {
    '$id': '/query/input',
    '$schema': constants.JSON_SCHEMA_URL,
    'title': 'Query input API JSON schema.'}
input.update(query)

output = {
    '$id': '/query/output',
    '$schema': constants.JSON_SCHEMA_URL,
    'title': 'Query output API JSON schema.',
    'type': 'object',
    'properties': {
        '$id': {'type': 'string', 'format': 'uri'},
        'timestamp': {'type': 'string', 'format': 'date-time'},
        'query': query,
        'sql': {'type': 'string'},
        'nrows': {'type': 'integer', 'mimimum': 0},
        'columns': {
            'type': 'array',
            'items': {'type': 'string'}
        },
        'cpu_time': {'type': 'number', 'mimimum': 0.0},
        'data': {
            'type': 'array',
            'items': {'type': 'object'}
        }
    },
    'required': [
        '$id',
        'timestamp',
        'query',
        'sql',
        'nrows',
        'columns',
        'cpu_time',
        'data'
    ],
    'additionalProperties': False
}
