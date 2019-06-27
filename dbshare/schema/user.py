"User API JSON schema."

from . import definitions
from .. import constants


schema = {
    '$id': constants.SCHEMA_BASE_URL + '/user',
    '$schema': constants.SCHEMA_SCHEMA_URL,
    'title': 'User API JSON schema.',
    'definitions': {'link': definitions.link},
    'type': 'object',
    'properties': {
        '$id': {'type': 'string', 'format': 'uri'},
        'timestamp': {'type': 'string', 'format': 'timestamp'},
        'username': {'type': 'string'},
        'email': {'type': 'string', 'format': 'email'},
        'role': {'type': 'string', 'enum': ['admin', 'user']},
        'status': {'type': 'string', 'enum': ['enabled', 'disabled']},
        'quota': {
            'oneOf': [
                {'type': 'integer', 'minimum': 0},
                {'type': 'null'}
            ]
        },
        'total_size': {'type': 'integer', 'minimum': 0},
        'modified': {'type': 'string', 'format': 'timestamp'},
        'created': {'type': 'string', 'format': 'timestamp'},
        'databases': {'$ref': '#/definitions/link'},
        'templates': {'$ref': '#/definitions/link'}
    },
    'required': [
        '$id',
        'timestamp',
        'username',
        'email',
        'role',
        'status',
        'quota',
        'total_size',
        'modified',
        'created',
        'databases',
        'templates'
    ],
    'additionalProperties': False
}
