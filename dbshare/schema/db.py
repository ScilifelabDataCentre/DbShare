"DbShare API db schema."

from . import definitions

schema = {
    '$id': 'http://dummy.org/', # To be updated when accessed.
    '$schema': 'http://json-schema.org/draft-07/schema#',
    'title': __doc__,
    'definitions': definitions.schema,
    'type': 'object',
    'properties': {
        '$id': {'type': 'string', 'format': 'uri'},
        'name': {'type': 'string'},
        'title': {'type': ['string', 'null']},
        'owner': {'$ref': '#/definitions/user'},
        'public': {'type': 'boolean'},
        'readonly': {'type': 'boolean'},
        'size': {'type': 'integer'},
        'modified': {'type': 'string', 'format': 'timestamp'},
        'created': {'type': 'string', 'format': 'timestamp'},
        'tables': {
            'type': 'array',
            'items': {
                'type': 'object',
                'properties': {
                    'name': {'type': 'string'},
                    'title': {'type': ['string', 'null']},
                    'api': {'$ref': '#/definitions/link'},
                    'database': {'$ref': '#/definitions/link'},
                    'nrows': {'type': ['number', 'null']},
                    'rows': {'$ref': '#/definitions/link'},
                    'data': {'$ref': '#/definitions/link'},
                    'display': {'$ref': '#/definitions/link'},
                    'visualizations': {
                        'type': 'array',
                        'items': {
                            'type': 'object'
                        }
                    }
                },
                'required': ['name', 
                             'title',
                             'api',
                             'database',
                             'nrows',
                             'rows',
                             'data',
                             'display',
                             'visualizations']
            }
        },
        'views': {
            'type': 'array',
            'items': {
                'type': 'object',
                'properties': {
                    'name': {'type': 'string'},
                    'title': {'type': ['string', 'null']},
                    'nrows': {'type': ['number', 'null']},
                    'rows': {'$ref': '#/definitions/link'},
                    'data': {'$ref': '#/definitions/link'},
                    'display': {'$ref': '#/definitions/link'},
                    'visualizations': {
                        'type': 'array',
                        'items': {
                            'type': 'object'
                        }
                    }
                },
                'required': [
                    'name', 'title', 'rows', 'data', 'display',
                ]
            }
        },
        'display': {'$ref': '#/definitions/link'},
        'home': {'$ref': '#/definitions/link'},
        'timestamp': {'type': 'string', 'format': 'timestamp'}
    },
    'required': ['name', 
                 'owner', 
                 'public',
                 'readonly', 
                 'size',
                 'modified',
                 'created',
                 'tables',
                 'display',
                 'home',
                 'timestamp']
}
