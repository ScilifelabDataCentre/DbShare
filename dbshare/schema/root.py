"API root JSON schema."

from . import definitions
from .. import constants


schema = {
    '$id': constants.SCHEMA_BASE_URL + 'root',
    '$schema': constants.SCHEMA_SCHEMA_URL,
    'timestamp': {'type': 'string', 'format': 'datetime'},
    'title': 'API root JSON schema.',
    'definitions': definitions.schema,
    'type': 'object',
    'properties': {
        '$id': {'type': 'string', 'format': 'uri'},
        'title': {'type': 'string'},
        'version': {'type': 'string',
                    'pattern': '^1\.[0-9]+\.[0-9]+$'},
        'databases': {
            'title': 'Links to collections of databases.',
            'type': 'object',
            'properties': {
                'all': {'title': 'Link to all databases.',
                        '$ref': '#/definitions/link'},
                'owner': {'title': 'Link to databases owned by the current user.',
                          '$ref': '#/definitions/link'},
                'public': {'title': 'Link to public databases.',
                           '$ref': '#/definitions/link'}},
            'required': ['public']
        },
        'templates': {
            'title': 'Links to collections of visualization templates.',
            'type': 'object',
            'properties': {
                'all': {'title': 'Link to all templates.',
                        '$ref': '#/definitions/link'},
                'owner': {'title': 'Link to templates owned by the current user.',
                          '$ref': '#/definitions/link'},
                'public': {'title': 'Link to public templates.',
                           '$ref': '#/definitions/link'}},
            'required': ['public']
        },
        'user': {'title': 'Link to the current user.',
                 '$ref': '#/definitions/user'},
        'schema': {'title': 'Link to the schema documents.',
                   '$ref': '#/definitions/link'}
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
