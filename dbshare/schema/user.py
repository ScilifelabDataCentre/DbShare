"DbShare API user schema."

from . import definitions

schema = {
    '$id': 'https://dbshare.scilifelab.se/api/schema/user',
    '$schema': 'http://json-schema.org/draft-07/schema#',
    'title': __doc__,
    'definitions': definitions.schema,
    'type': 'object',
    'properties': {
        '$id': {'type': 'string', 'format': 'uri'},
        'username': {'type': 'string'},
        'email': {'type': 'string', 'format': 'email'},
        'role': {'type': 'string', 'enum': ['admin', 'user']},
        'status': {'type': 'string', 'enum': ['enabled', 'disabled']},
        'total_size': {'type': 'integer', 'minimum': 0},
        'modified': {'type': 'string', 'format': 'timestamp'},
        'created': {'type': 'string', 'format': 'timestamp'},
        'databases': {'$ref': '#/definitions/link'},
        'templates': {'$ref': '#/definitions/link'},
        'timestamp': {'type': 'string', 'format': 'timestamp'}
    },
    'required': [
        '$id',
        'username',
        'email',
        'role',
        'status',
        'total_size',
        'modified',
        'created',
        'databases',
        'templates',
        'timestamp'
    ]
}
