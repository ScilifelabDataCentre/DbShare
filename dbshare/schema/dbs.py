"JSON schema for the map of databases."

from . import definitions

schema = {
    '$id': 'https://dbshare.scilifelab.se/api/schema/dbs',
    '$schema': 'http://json-schema.org/draft-07/schema#',
    'title': __doc__,
    'definitions': definitions.schema,
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
                    'href': {'type': 'string', 'format': 'uri'}
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
