"Database API JSON schema."

from . import definitions
from .. import constants


schema = {
    '$id': constants.SCHEMA_BASE_URL + '/db',
    '$schema': constants.SCHEMA_SCHEMA_URL,
    'title': 'Database API JSON schema.',
    'definitions': {
        'link': definitions.link,
        'iobody': definitions.iobody},
    'type': 'object',
    'properties': {
        '$id': {'type': 'string', 'format': 'uri'},
        'timestamp': {'type': 'string', 'format': 'timestamp'},
        'name': {'type': 'string'},
        'title': {'type': ['string', 'null']},
        'description': {'type': ['string', 'null']},
        'owner': definitions.user,
        'public': {'type': 'boolean'},
        'readonly': {'type': 'boolean'},
        'size': {'type': 'integer', 'minimum': 0},
        'modified': {'type': 'string', 'format': 'timestamp'},
        'created': {'type': 'string', 'format': 'timestamp'},
        'hashes': {'type': 'object'},
        'tables': {
            'type': 'array',
            'items': {
                'type': 'object',
                'properties': {
                    'name': {'type': 'string'},
                    'title': {'type': ['string', 'null']},
                    'href': {'type': 'string', 'format': 'uri'},
                    'database': {'$ref': '#/definitions/link'},
                    'nrows': {'type': ['number', 'null']},
                    'rows': {'$ref': '#/definitions/link'},
                    'data': {'$ref': '#/definitions/link'},
                    'visualizations': {
                        'type': 'array',
                        'items': {
                            'type': 'object'
                        }
                    }
                },
                'required': ['name', 
                             'title',
                             'href',
                             'database',
                             'nrows',
                             'rows',
                             'data']
            }
        },
        'views': {
            'type': 'array',
            'items': {
                'type': 'object',
                'properties': {
                    'name': {'type': 'string'},
                    'title': {'type': ['string', 'null']},
                    'href': {'type': 'string', 'format': 'uri'},
                    'database': {'$ref': '#/definitions/link'},
                    'nrows': {'type': ['number', 'null']},
                    'rows': {'$ref': '#/definitions/link'},
                    'data': {'$ref': '#/definitions/link'},
                    'visualizations': {
                        'type': 'array',
                        'items': {
                            'type': 'object'
                        }
                    }
                },
                'required': ['name',
                             'title',
                             'href',
                             'database',
                             'nrows',
                             'rows',
                             'data']
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
    ]
}

edit = {
    '$id': constants.SCHEMA_BASE_URL + '/db/edit',
    '$schema': constants.SCHEMA_SCHEMA_URL,
    'title': 'Database edit API JSON schema.',
    'type': 'object',
    'properties': {
        'name': {'type': 'string'},
        'title': {'type': ['string', 'null']},
        'description': {'type': ['string', 'null']},
        'public': {'type': 'boolean'}
    }
}
