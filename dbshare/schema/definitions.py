"JSON schema definitions components."

link = {
    'title': 'A link to an object.',
    'type': 'object',
    'properties': {
        'title': {'type': 'string'},
        'href': {'type': 'string', 'format': 'uri'},
        'content-type': {'type': 'string', 'default': 'application/json'},
        'format': {'type': 'string', 'default': 'json'}
    },
    'required': [
        'href'
    ]
}

user = {
    'title': 'The user associated with the current object.',
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

iobody = {
    'title': 'Input/output data body.',
    'type': 'object',
    'properties': {
        'content-type': {'type': 'string'},
        'schema': {
            'title': 'JSON schema of data body content.',
            'type': 'object',
            'properties': {
                'href': {'type': 'string', 'format': 'uri'}
            },
            'required': ['href']
        }
    },
    'required': ['content-type']
}

io = {
    'oneOf': [
        {'$ref': '#/definitions/iobody'},
        {'type': 'array',
         'items': {'$ref': '#/definitions/iobody'}
        }
    ]
}

operations = {
    'title': 'Operations for modifying the DbShare server data.',
    'type': 'object',
    'propertyNames': property_names,
    'additionalProperties': {
        'title': 'The property name is the type of entity operated on.',
        'type': 'object',
        'propertyNames': property_names,
        'additionalProperties': {
            'title': 'The property name is the operation.',
            'type': 'object',
            'properties': {
                'title': {'type': 'string'},
                'href': {'type': 'string', 'format': 'uri'},
                'variables': {
                    'type': 'object'
                },
                'method': {
                    'type': 'string',
                    'enum': ['POST', 'PUT', 'DELETE']
                },
                'input': io,
                'output': io,
            },
            'required': ['href', 'method']
        }
    }
}
