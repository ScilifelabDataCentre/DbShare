"Rows API (from table or view) schema."

from . import definitions

schema = {
    '$id': 'https://dbshare.scilifelab.se/api/schema/table',
    '$schema': 'http://json-schema.org/draft-07/schema#',
    'title': __doc__,
    'definitions': definitions.schema,
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
    ]
}
