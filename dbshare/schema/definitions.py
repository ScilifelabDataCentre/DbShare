"JSON schema definitions components."

link_def = {
    'title': 'A link to an object.',
    'type': 'object',
    'properties': {
        'href': {'type': 'string', 'format': 'uri'},
        'content_type': {'type': 'string', 'default': 'application/json'},
        'format': {'type': 'string', 'default': 'json'}
    },
    'required': [
        'href'
    ]
}

user_def = {
    'title': 'The owner of the current object.',
    'type': 'object',
    'properties': {
        'username': {'type': 'string'},
        'href': {'type': 'string', 'format': 'uri'}
    },
    'required': [
        'username',
        'href'
    ]
}

property_names = {'pattern': '^[a-zA-Z][a-zA-Z0-9_-]*$'}

operation_def = {
    'title': 'An operation to modify the content of the DbShare server.',
    'type': 'object',
    'properties': {
        'title': {'type': 'string'},
        'href': {'type': 'string', 'format': 'uri-template'},
        'variables': {
            'type': 'object',
            'propertyNames': property_names,
            'additionalProperties': {
                'type': 'object',
                'properties': {
                    'title': {'type': 'string'},
                    'type': {'type': 'string',
                             'enum': ['string']
                    }
                }
            }
        },
        'method': {
            'type': 'string',
            'enum': ['PUT', 'POST', 'DELETE']
        },
        'input': {
            'oneOf': [
                {'type': 'boolean'},
                {'type': 'object',
                 'properties': {
                     'contentType': {'type': 'string'},
                     'schema': {'type': 'string', 'format': 'uri'}
                 }
                }
            ]
        }
    }
}
