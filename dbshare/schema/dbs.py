"Databases map API JSON schema."

from . import definitions
from .. import constants


schema = {
    '$id': constants.SCHEMA_BASE_URL + '/dbs',
    '$schema': constants.SCHEMA_SCHEMA_URL,
    'title': 'Databases map API JSON schema.',
    'definitions': {
        'user': definitions.user
    },
    'type': 'object',
    'properties': {
        '$id': {'type': 'string', 'format': 'uri'},
        'timestamp': {'type': 'string', 'format': 'timestamp'},
        'title': {'type': 'string'},
        'user': {'$ref': '#/definitions/user'},
        'total_size': {'type': 'integer', 'minimum': 0},
        'databases': {
            'type': 'array',
            'items': {
                'type': 'object',
                'properties': {
                    'name': {'type': 'string'},
                    'title': {'type': ['string', 'null']},
                    'description': {'type': ['string', 'null']},
                    'owner': {'$ref': '#/definitions/user'},
                    'public': {'type': 'boolean'},
                    'readonly': {'type': 'boolean'},
                    'size': {'type': 'integer'},
                    'modified': {'type': 'string', 'format': 'timestamp'},
                    'created': {'type': 'string', 'format': 'timestamp'},
                    'hashes': definitions.hashes,
                    'href': {'type': 'string', 'format': 'uri'},
                    'operations': definitions.operations
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
                ],
                'additionalProperties': False
            }
        }
    },
    'required': [
        '$id',
        'timestamp',
        'title',
        'databases'
    ],
    'additionalProperties': False
}
