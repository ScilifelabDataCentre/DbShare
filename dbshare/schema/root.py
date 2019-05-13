"DbShare API root schema."

schema = {
    '$id': 'https://dbshare.scilifelab.se/api/schema/root.json',
    '$schema': 'http://json-schema.org/draft-07/schema#',
    'title': __doc__,
    'type': 'object',
    'definitions': {
        'link': {
            'type': 'object',
            'properties': {
                'href': {'type': 'string', 'format': 'uri'},
                'format': {'type': 'string', 'default': ' json'}
            },
            'required': ['href']
        }
    },
    'required': ['$id',
                 'title',
                 'version',
                 'databases',
                 'templates',
                 'display',
                 'timestamp'],
    'properties': {
        '$id': {'type': 'string', 'format': 'uri'},
        'title': {'type': 'string'},
        'version': {'type': 'string',
                    'pattern': '^1\.[0-9]+\.[0-9]+$'},
        'databases': {'type': 'object',
                      'properties': {'all': {'$ref': '#/definitions/link'},
                                     'owner': {'$ref': '#/definitions/link'},
                                     'public': {'$ref': '#/definitions/link'}},
                      'required': ['public', 'all']
        },
        'templates': {'type': 'object',
                      'properties': {'all': {'$ref': '#/definitions/link'},
                                     'owner': {'$ref': '#/definitions/link'},
                                     'public': {'$ref': '#/definitions/link'}},
                      'required': ['public', 'all']
        },
        'display': {'$ref': '#/definitions/link'},
        'user': {'type': 'object',
                 'properties': {'username': {'type': 'string'},
                                'href': {'type': 'string', 'format': 'uri'}},
                 'required': ['username', 'href']
        },
        'timestamp': {'type': 'string', 'format': 'datetime'}
    }
}
