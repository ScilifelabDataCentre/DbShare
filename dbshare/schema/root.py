"DbShare API root schema."

from . import definitions

schema = {
    '$id': 'http://dummy.org/', # To be updated when accessed.
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
        'display': {'$ref': '#/definitions/link'},
        'user': {'$ref': '#/definitions/user'},
        'timestamp': {'type': 'string', 'format': 'datetime'}
    },
    'required': ['$id',
                 'title',
                 'version',
                 'databases',
                 'templates',
                 'display',
                 'timestamp']
}
