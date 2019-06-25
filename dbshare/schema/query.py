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
        }
    },
    'required': [
        'select',
        'from'
    ]
}

input = {
    '$id': constants.SCHEMA_BASE_URL + '/query/input',
    '$schema': constants.SCHEMA_SCHEMA_URL,
    'title': 'Query input API JSON schema.'}
input.update(query)

output = {
    '$id': constants.SCHEMA_BASE_URL + '/query/output',
    '$schema': constants.SCHEMA_SCHEMA_URL,
    'title': 'Query output API JSON schema.',
    'type': 'object',
    'properties': {
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
        },
    },
    'required': [
        'query',
        'sql',
        'nrows',
        'columns',
        'cpu_time',
        'data'
    ]
}
