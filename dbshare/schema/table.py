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
            'notnull': {'type': 'boolean'},
            'unique': {'type': 'boolean'},
            'statistics': {
                'type': 'object',
                'propertyNames': definitions.property_names,
                'additionalProperties': {
                    'type': 'object',
                    'properties': {
                        'value': {},
                        'title': {'type': 'string'},
                        'info': {}
                    },
                    'required': ['value'],
                    'additionalProperties': False
                }
            },
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
        'statistics': {'$ref': '#/definitions/link'},
        'columns': columns,
        # 'visualizations': definitions.visualizations,
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
        'columns',
        # 'visualizations',
        'indexes'
    ],
    'additionalProperties': False
}

statistics = {
    '$id': constants.SCHEMA_BASE_URL + '/table/statistics',
    '$schema': constants.SCHEMA_SCHEMA_URL,
    'title': 'Table API JSON statistics.',
    'definitions': {'link': definitions.link},
    'type': 'object',
    'properties': {
        '$id': {'type': 'string', 'format': 'uri'},
        'timestamp': {'type': 'string', 'format': 'date-time'},
        'name': {'type': 'string'},
        'nrows': {'type': 'integer', 'minimum': 0},
        'rows': {'$ref': '#/definitions/link'},
        'data': {'$ref': '#/definitions/link'},
        'href': {'type': 'string', 'format': 'uri'},
        'columns': columns
    },
    'required': [
        '$id',
        'timestamp',
        'name', 
        'nrows',
        'rows',
        'data',
        'href',
        'columns'
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
