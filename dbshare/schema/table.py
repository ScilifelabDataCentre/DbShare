"Table API JSON schema."

from . import definitions
from .. import constants


columns = {
    'type': 'array',
    'items': {
        'type': 'object',
        'properties': {
            'name': {'type': 'string'},
            'type': {'type': 'string',
                     'enum': ['INTEGER', 'REAL', 'TEXT', 'BLOB']},
            'primarykey': {'type': 'boolean'},
            'notnull': {'type': 'boolean'}
        },
        'required': ['name', 'type'],
        'additionalProperties': False
    }
}

indexes = {
    'type': 'array',
    'items': {
        'type': 'object',
        'properties': {
            'name': {'type': 'string'},
            'unique': {'type': 'boolean'},
            'columns': {
                'type': 'array',
                'items': {'type': 'string'}
            }
        },
        'required': ['unique', 'columns'],
        'additionalProperties': False
    }
}

schema = {
    '$id': constants.SCHEMA_BASE_URL + '/table',
    '$schema': constants.SCHEMA_SCHEMA_URL,
    'title': 'Table API JSON schema.',
    'definitions': {'link': definitions.link},
    'type': 'object',
    'properties': {
        '$id': {'type': 'string', 'format': 'uri'},
        'timestamp': {'type': 'string', 'format': 'date-time'},
        'name': {'type': 'string'},
        'title': {'type': ['string', 'null']},
        'description': {'type': ['string', 'null']},
        'database': {'$ref': '#/definitions/link'},
        'nrows': {'type': 'integer', 'minimum': 0},
        'rows': {'$ref': '#/definitions/link'},
        'data': {'$ref': '#/definitions/link'},
        'visualizations': definitions.visualizations,
        'columns': columns,
        'indexes': indexes
    },
    'required': [
        '$id',
        'timestamp',
        'name', 
        'database',
        'nrows',
        'rows',
        'data',
        'visualizations',
        'columns',
        'indexes'
    ],
    'additionalProperties': False
}

create = {
    '$id': constants.SCHEMA_BASE_URL + '/table/create',
    '$schema': constants.SCHEMA_SCHEMA_URL,
    'title': 'API JSON schema for creating a table.',
    'type': 'object',
    'properties': {
        'name': {'type': 'string'},
        'title': {'type': ['string', 'null']},
        'description': {'type': ['string', 'null']},
        'columns': columns,
        'indexes': indexes
    },
    'required': ['name', 'columns']
}

input = {
    '$id': constants.SCHEMA_BASE_URL + '/table/input',
    '$schema': constants.SCHEMA_SCHEMA_URL,
    'title': 'JSON schema for table data input.',
    'type': 'object',
    'properties': {
        'data': {
            'type': 'array',
            'items': {'type': 'object'}
        }
    },
    'required': ['data']
}
