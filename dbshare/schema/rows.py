"Rows data (table or view) API JSON schema."

from .. import constants


schema = {
    '$id': constants.SCHEMA_BASE_URL + '/rows',
    '$schema': constants.SCHEMA_SCHEMA_URL,
    'title': 'Rows data (table or view) API JSON schema.',
    'type': 'object',
    'properties': {
        '$id': {'type': 'string', 'format': 'uri'},
        'name': {'type': 'string'},
        'title': {'type': ['string', 'null']},
        'source': {
            'type': 'object',
            'properties': {
                'type': {'type': 'string', 'enum': ['table', 'view']},
                'href': {'type': 'string', 'format': 'uri'}
            },
        },
        'nrows': {
            'oneOf': [
                {'type': 'null'},
                {'type': 'integer', 'minimum': 0}
            ]
        },
        'data': {
            'type': 'array',
            'items': {'type': 'object'}
        },
        'timestamp': {'type': 'string', 'format': 'timestamp'}
    },
    'required': [
        '$id',
        'name',
        'source',
        'nrows',
        'data',
        'timestamp'
    ],
    'additionalProperties': False
}
