"Root API schema."

from . import definitions

schema = {
    '$id': 'https://dbshare.scilifelab.se/api/schema/root',
    '$schema': 'http://json-schema.org/draft-07/schema#',
    'title': __doc__,
    'definitions': definitions.schema,
    'type': 'object',
    'properties': {
        '$id': {'type': 'string', 'format': 'uri'},
        'title': {'type': 'string'},
        'version': {'type': 'string',
                    'pattern': '^1\.[0-9]+\.[0-9]+$'},
        'databases': {'type': 'object',
                      'properties': {
                          'all': {'$ref': '#/definitions/link'},
                          'owner': {'$ref': '#/definitions/link'},
                          'public': {'$ref': '#/definitions/link'}},
                      'required': ['public']
        },
        'templates': {'type': 'object',
                      'properties': {
                          'all': {'$ref': '#/definitions/link'},
                          'owner': {'$ref': '#/definitions/link'},
                          'public': {'$ref': '#/definitions/link'}},
                      'required': ['public']
        },
        'user': {'$ref': '#/definitions/user'},
        'timestamp': {'type': 'string', 'format': 'datetime'}
    },
    'required': [
        '$id',
        'title',
        'version',
        'databases',
        'templates',
        'timestamp'
    ]
}
