"User list API JSON schema."

from . import definitions
from .. import constants


schema = {
    '$id': constants.SCHEMA_BASE_URL + '/users',
    '$schema': constants.JSON_SCHEMA_URL,
    'title': 'User list API JSON schema.',
    'type': 'object',
    'properties': {
        '$id': {'type': 'string', 'format': 'uri'},
        'timestamp': {'type': 'string', 'format': 'date-time'},
        'title': {'type': 'string'},
        'users': {
            'type': 'array',
            'items': {
                'type': 'object',
                'properties': {
                    'username': {'type': 'string'},
                    'email': {'type': 'string', 'format': 'email'},
                    'role': {'type': 'string', 'enum': ['admin', 'user']},
                    'status': {
                        'type': 'string', 
                        'enum': ['enabled', 'disabled']
                    },
                    'modified': {'type': 'string', 'format': 'date-time'},
                    'created': {'type': 'string', 'format': 'date-time'},
                    'href': {'type': 'string', 'format': 'uri'}
                },
                'required': [
                    'username',
                    'email',
                    'role',
                    'status',
                    'modified',
                    'created',
                    'href'
                ],
                'additionalProperties': False
            }
        }
    },
    'required': [
        '$id',
        'timestamp',
        'title',
        'users'
    ],
    'additionalProperties': False
}
