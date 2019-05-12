"DbPortal API dbs schema."

schema = {
    '$id': 'https://dbportal.scilifelab.se/api/schema/dbs.json',
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
        },
        'user': {
            'type': 'object',
            'properties':
            {'username': {'type': 'string'},
             'href': {'type': 'string', 'format': 'uri'}
            },
            'required': ['username', 'href']
        }
    },
    'properties': {
        '$id': {'type': 'string', 'format': 'uri'},
        'title': {'type': 'string'},
        'owner': {'$ref': '#/definitions/user'},
        'total_size': {'type': 'integer'},
        'databases': {
            'type': 'array',
            'items': {
                'type': 'object',
                'properties': {'name': {'type': 'string'},
                               'title': {'type': ['string', 'null']},
                               'owner': {'$ref': '#/definitions/user'},
                               'public': {'type': 'boolean'},
                               'readonly': {'type': 'boolean'},
                               'size': {'type': 'integer'},
                               'modified': {'type': 'string',
                                            'format': 'timestamp'},
                               'created': {'type': 'string',
                                           'format': 'timestamp'},
                               'href': {'type': 'string', 'format': 'uri'}
                },
                'required': ['name',
                             'title',
                             'owner',
                             'public',
                             'readonly',
                             'size',
                             'modified',
                             'created',
                             'href']
            }
        },
        'display': {'$ref': '#/definitions/link'},
        'api': {'$ref': '#/definitions/link'},
        'timestamp': {'type': 'string', 'format': 'timestamp'}
    },
    'required': ['title', 'databases', 'display', 'api', 'timestamp']
}
