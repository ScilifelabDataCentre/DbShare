"JSON schema for the API root."

from . import definitions
from .. import constants


schema = {
    '$id': constants.SCHEMA_BASE_URL + 'root',
    '$schema': constants.SCHEMA_SCHEMA_URL,
    'timestamp': {'type': 'string', 'format': 'datetime'},
    'title': 'JSON schema for the API root.',
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
        'schema': {'$ref': '#/definitions/link'}
    },
    'required': [
        '$id',
        'timestamp',
        'title',
        'version',
        'databases',
        'templates',
        'schema'
    ]
}
