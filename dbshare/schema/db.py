"Database API JSON schema."

from . import definitions
from .. import constants


schema = {
    '$id': constants.SCHEMA_BASE_URL + '/db',
    '$schema': constants.SCHEMA_SCHEMA_URL,
    'title': 'Database API JSON schema.',
    'definitions': {
        'link': definitions.link,
        'iobody': definitions.iobody,
        'visualizations': definitions.visualizations
    },
    'type': 'object',
    'properties': {
        '$id': {'type': 'string', 'format': 'uri'},
        'timestamp': {'type': 'string', 'format': 'date-time'},
        'name': {'type': 'string'},
        'title': {'type': ['string', 'null']},
        'description': {'type': ['string', 'null']},
        'owner': definitions.user,
        'public': {'type': 'boolean'},
        'readonly': {'type': 'boolean'},
        'size': {'type': 'integer', 'minimum': 0},
        'modified': {'type': 'string', 'format': 'date-time'},
        'created': {'type': 'string', 'format': 'date-time'},
        'hashes': definitions.hashes,
        'tables': {
            'title': 'The list of tables in the database.',
            'type': 'array',
            'items': {
                'type': 'object',
                'properties': {
                    'name': {'type': 'string'},
                    'title': {'type': ['string', 'null']},
                    'description': {'type': ['string', 'null']},
                    'href': {'type': 'string', 'format': 'uri'},
                    'database': {'$ref': '#/definitions/link'},
                    'nrows': {'type': ['number', 'null']},
                    'rows': {'$ref': '#/definitions/link'},
                    'data': {'$ref': '#/definitions/link'},
                    'visualizations': {'$ref': '#/definitions/visualizations'}
                },
                'required': ['name', 
                             'title',
                             'description',
                             'href',
                             'database',
                             'nrows',
                             'rows',
                             'data'],
                'additionalProperties': False
            }
        },
        'views': {
            'title': 'The list of views in the database.',
            'type': 'array',
            'items': {
                'type': 'object',
                'properties': {
                    'name': {'type': 'string'},
                    'title': {'type': ['string', 'null']},
                    'description': {'type': ['string', 'null']},
                    'href': {'type': 'string', 'format': 'uri'},
                    'database': {'$ref': '#/definitions/link'},
                    'nrows': {'type': ['number', 'null']},
                    'rows': {'$ref': '#/definitions/link'},
                    'data': {'$ref': '#/definitions/link'},
                    'visualizations': {'$ref': '#/definitions/visualizations'}
                },
                'required': ['name',
                             'title',
                             'description',
                             'href',
                             'database',
                             'nrows',
                             'rows',
                             'data'],
                'additionalProperties': False
            }
        },
        'operations': definitions.operations
    },
    'required': [
        '$id',
        'timestamp',
        'name', 
        'title',
        'description',
        'owner',
        'public',
        'readonly', 
        'size',
        'modified',
        'created',
        'tables'
    ],
    'additionalProperties': False
}

edit = {
    '$id': constants.SCHEMA_BASE_URL + '/db/edit',
    '$schema': constants.SCHEMA_SCHEMA_URL,
    'title': 'API JSON schema for editing the database metadata.',
    'type': 'object',
    'properties': {
        'name': {'type': 'string'},
        'title': {'type': ['string', 'null']},
        'description': {'type': ['string', 'null']},
        'public': {'type': 'boolean'}
    },
    'additionalProperties': False
}
