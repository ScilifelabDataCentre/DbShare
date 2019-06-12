"JSON schema for the query API."

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
    '$id': constants.SCHEMA_BASE_URL + 'query_input',
    '$schema': constants.SCHEMA_SCHEMA_URL,
    'title': 'JSON schema for the query API input.'}
input.update(query)

output = {
    '$id': constants.SCHEMA_BASE_URL + 'query',
    '$schema': constants.SCHEMA_SCHEMA_URL,
    'title': 'JSON schema for the query API output.',
    'type': 'object',
    'properties': {
        'query': query,
        'sql': {'type': 'string'},
        'nrows': {'type': 'integer', 'mimimum': 0},
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
        'cpu_time',
        'data'
    ]
}
