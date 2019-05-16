"Dbs API schema."

from . import definitions
from . import database

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
            'items': database.schema # Part only; completed below.
        },
        'timestamp': {'type': 'string', 'format': 'timestamp'}
    },
    'required': [
        'title',
        'databases',
        'timestamp'
    ]
}

items = schema['properties']['databases']['items']
items['properties']['href'] = {'type': 'string', 'format': 'uri'}
items['required'].append('href')
