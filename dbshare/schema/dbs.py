"Databases map API JSON schema."

from . import definitions
from .. import constants


schema = {
    '$id': constants.SCHEMA_BASE_URL + '/dbs',
    '$schema': constants.SCHEMA_SCHEMA_URL,
    'title': 'Databases map API JSON schema.',
    'definitions': {
        'user': definitions.user_def,
        'operation': definitions.operation_def
    },
    'type': 'object',
    'properties': {
        '$id': {'type': 'string', 'format': 'uri'},
        'title': {'type': 'string'},
        'owner': {'$ref': '#/definitions/user'},
        'total_size': {'type': 'integer', 'minimum': 0},
        'databases': {
            'type': 'array',
            'items': {
                'type': 'object',
                'properties': {
                    'name': {'type': 'string'},
                    'title': {'type': ['string', 'null']},
                    'owner': {'$ref': '#/definitions/user'},
                    'public': {'type': 'boolean'},
                    'readonly': {'type': 'boolean'},
                    'size': {'type': 'integer'},
                    'modified': {'type': 'string', 'format': 'timestamp'},
                    'created': {'type': 'string', 'format': 'timestamp'},
                    'href': {'type': 'string', 'format': 'uri'},
                    'operations': {
                        'create': {'$ref': '#/definitions/operation'}
                    }
                },
                'required': [
                    'name',
                    'title',
                    'owner',
                    'public',
                    'readonly',
                    'size',
                    'modified',
                    'created',
                    'href'
                ]
            }
        },
        'timestamp': {'type': 'string', 'format': 'timestamp'}
    },
    'required': [
        'title',
        'databases',
        'timestamp'
    ]
}
