"Table API schema."

from . import definitions
from . import visualization
from . import column

schema = {
    '$id': 'https://dbshare.scilifelab.se/api/schema/table',
    '$schema': 'http://json-schema.org/draft-07/schema#',
    'title': __doc__,
    'definitions': definitions.schema,
    'type': 'object',
    'properties': {
        '$id': {'type': 'string', 'format': 'uri'},
        'name': {'type': 'string'},
        'title': {'type': ['string', 'null']},
        'description': {'type': ['string', 'null']},
        'database': {'$ref': '#/definitions/link'},
        'nrows': {'type': 'integer', 'minimum': 0},
        'rows': {'$ref': '#/definitions/link'},
        'data': {'$ref': '#/definitions/link'},
        'visualizations': {
            'type': 'array',
            'items': visualization.schema},
        'columns': {
            'type': 'array',
            'items': column.schema},
        'timestamp': {'type': 'string', 'format': 'timestamp'}
    },
    'required': [
        '$id',
        'name', 
        'database',
        'nrows',
        'rows',
        'data',
        'visualizations',
        'columns',
        'timestamp'
    ]
}

# Table specification for creation.
schema_spec = {
    '$id': 'https://dbshare.scilifelab.se/api/schema/table_create',
    '$schema': 'http://json-schema.org/draft-07/schema#',
    'title': 'Table creation API schema.',
    'type': 'object',
    'properties': {
        'name': {'type': 'string'},
        'title': {'type': ['string', 'null']},
        'description': {'type': ['string', 'null']},
        'columns': {
            'type': 'array',
            'items': column.schema}
    },
    'required': [
        'name', 
        'columns'
    ]
}

# Specification of rows data for the table.
schema_data = {
    '$id': 'https://dbshare.scilifelab.se/api/schema/table_data',
    '$schema': 'http://json-schema.org/draft-07/schema#',
    'title': 'Table data API schema.',
    'type': 'object',
    'properties': {
        'data': {
            'type': 'array',
            'items': {'type': 'object'}
        }
    },
    'required': [
        'data'
    ]
}
