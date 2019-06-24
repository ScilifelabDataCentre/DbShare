"View API JSON schema."

from . import definitions
from . import query
from . import visualization
from .. import constants

schema = {
    '$id': constants.SCHEMA_BASE_URL + '/view',
    '$schema': constants.SCHEMA_SCHEMA_URL,
    'title': 'View API JSON schema.',
    'definitions': {'link': definitions.link},
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
            'items': visualization.spec},
        'query': query.query,
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
