"DbShare API db schema."

schema = {
    '$id': 'http://dummy.org/', # To be updated when accessed.
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
        'name': {'type': 'string'},
        'title': {'type': ['string', None]},
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
                'properties': {'name': {'type': 'string'},
                               'title': {'type': ['string', 'null']},
                               'href': {'type': 'string', 'format': 'uri'}
                },
                'required': ['name', 
                             'title',
                             'href']
            }
        },
        'views': {
            'type': 'array',
            'items': {
                'type': 'object',
                'properties': {
                    'name': {'type': 'string'},
                    'title': {'type': ['string', 'null']},
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
        'api': {'$ref': '#/definitions/link'},
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
                 'api',
                 'timestamp']
}
