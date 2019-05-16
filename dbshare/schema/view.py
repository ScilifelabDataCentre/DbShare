"View API schema."

from . import definitions
from . import visualization

schema = {
    '$id': 'https://dbshare.scilifelab.se/api/schema/view',
    '$schema': 'http://json-schema.org/draft-07/schema#',
    'title': __doc__,
    'definitions': definitions.schema,
    'type': 'object',
    'properties': {
        '$id': {'type': 'string', 'format': 'uri'},
        'name': {'type': 'string'},
        'title': {'type': ['string', 'null']},
        'database': {'$ref': '#/definitions/link'},
        'nrows': {
            'oneOf': [
                {'type': 'null'},
                {'type': 'integer', 'minimum': 0}
            ]
        },
        'rows': {'$ref': '#/definitions/link'},
        'data': {'$ref': '#/definitions/link'},
        'visualizations': {
            'type': 'array',
            'items': visualization.schema},
        'query': {
            'type': 'object'
        },
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
        'query',
        'timestamp'
    ]
}
