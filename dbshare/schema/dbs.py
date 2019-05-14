"DbShare API dbs schema."

from . import definitions
from . import database

schema = {
    '$id': 'http://dummy.org/', # To be updated when accessed.
    '$schema': 'http://json-schema.org/draft-07/schema#',
    'title': __doc__,
    'definitions': definitions.schema,
    'type': 'object',
    'properties': {
        '$id': {'type': 'string', 'format': 'uri'},
        'title': {'type': 'string'},
        'owner': {'$ref': '#/definitions/user'},
        'total_size': {'type': 'integer'},
        'databases': {
            'type': 'array',
            'items': database.schema
        },
        'display': {'$ref': '#/definitions/link'},
        'home': {'$ref': '#/definitions/link'},
        'timestamp': {'type': 'string', 'format': 'timestamp'}
    },
    'required': ['title',
                 'databases',
                 'display',
                 'home',
                 'timestamp']
}
