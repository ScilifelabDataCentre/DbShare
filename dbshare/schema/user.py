"JSON schema for the User API."

from . import definitions
from .. import constants


schema = {
    '$id': constants.SCHEMA_BASE_URL + 'user',
    '$schema': constants.SCHEMA_SCHEMA_URL,
    'title': __doc__,
    'definitions': definitions.schema,
    'type': 'object',
    'properties': {
        '$id': {'type': 'string', 'format': 'uri'},
        'username': {'type': 'string'},
        'email': {'type': 'string', 'format': 'email'},
        'role': {'type': 'string', 'enum': ['admin', 'user']},
        'status': {'type': 'string', 'enum': ['enabled', 'disabled']},
        'total_size': {'type': 'integer', 'minimum': 0},
        'modified': {'type': 'string', 'format': 'timestamp'},
        'created': {'type': 'string', 'format': 'timestamp'},
        'databases': {'$ref': '#/definitions/link'},
        'templates': {'$ref': '#/definitions/link'},
        'timestamp': {'type': 'string', 'format': 'timestamp'}
    },
    'required': [
        '$id',
        'username',
        'email',
        'role',
        'status',
        'total_size',
        'modified',
        'created',
        'databases',
        'templates',
        'timestamp'
    ]
}
