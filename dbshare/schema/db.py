"JSON schema for the database API."

from . import definitions
from .. import constants

# XXX edit?
input = {
    '$id': constants.SCHEMA_BASE_URL + 'db',
    '$schema': constants.SCHEMA_SCHEMA_URL,
    'title': 'JSON schema for the database API input.',
    'type': 'object',
    'properties': {
        'name': {'type': 'string'},
        'title': {'type': ['string', 'null']},
        'description': {'type': ['string', 'null']},
        'public': {'type': 'boolean'}
    }
}

# XXX schema?
output = {
    '$id': constants.SCHEMA_BASE_URL + 'db',
    '$schema': constants.SCHEMA_SCHEMA_URL,
    'title': 'JSON schema for the database API output.',
    'definitions': definitions.schema,
    'type': 'object',
    'properties': {
        '$id': {'type': 'string', 'format': 'uri'},
        'name': {'type': 'string'},
        'title': {'type': ['string', 'null']},
        'description': {'type': ['string', 'null']},
        'owner': {'$ref': '#/definitions/user'},
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
        'timestamp': {'type': 'string', 'format': 'timestamp'}
    },
    'required': [
        '$id',
        'name', 
        'title',
        'description',
        'owner',
        'public',
        'readonly', 
        'size',
        'modified',
        'created',
        'tables',
        'timestamp'
    ]
}
